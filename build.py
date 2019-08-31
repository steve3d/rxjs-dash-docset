#!/usr/bin/env python3

import glob
import json
import os
import re
import shutil
import sqlite3
import sys
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader


class Builder:
    def __init__(self, target):
        self.env = Environment(loader=FileSystemLoader(os.path.join(os.getcwd(), 'templates')))
        self.target = target
        self.cwd = os.getcwd()
        self.output = os.path.join(os.getcwd(), 'output')
        self.source = os.path.join(os.path.realpath(target), 'docs_app')
        self.generated = os.path.join(os.path.realpath(target), 'docs_app/dist')
        self.guide_template = self.env.get_template('guide.html')
        self.api_template = self.env.get_template('api.html')
        self.api_list = self.env.get_template('api-list-container.html')

    def clean_output(self):
        if os.path.isdir(self.output):
            shutil.rmtree(self.output)

        os.mkdir(self.output)
        shutil.copytree(os.path.join(self.cwd, 'assets'), os.path.join(self.output, 'assets'))
        shutil.copytree(os.path.join(self.source, 'dist', 'assets', 'images'), os.path.join(self.output, 'assets', 'images'))

    def copy_stylesheet(self):
        g = glob.glob(os.path.join(os.path.join(self.source, 'dist'), '*.css'))
        if len(g) > 0:
            style = glob.glob(os.path.join(os.path.join(self.source, 'dist'), '*.css'))[0]
            shutil.copy(style, os.path.join(self.output, 'assets'))
            self.stylesheet = 'assets/' + os.path.basename(style)

    def create_folder(self, id):
        dir = os.path.join(self.output, os.path.dirname(id))
        if os.path.isdir(dir) == False:
            os.makedirs(dir)

    def write_template(self, id, title, content):
        filePath = os.path.join(self.output, id + '.html')
        folder = os.path.dirname(filePath)
        with open(filePath, 'wt') as o:
            baseUrl = '../' * id.count('/')
            if baseUrl == '':
                baseUrl = './'

            o.write(self.api_template.render(title=title, content=content,
                                             baseUrl=baseUrl,
                                             style=self.stylesheet))



    def build_rxjs(self):
        os.chdir(self.source)
        if not os.path.isdir(os.path.join(self.source, 'node_modules')):
            shutil.rmtree(os.path.join(self.source, 'node_modules'))
            os.unlink(os.path.join(self.source, 'package-lock.json'))
            os.spawnlp(os.P_WAIT, 'npm', 'npm', 'install')
        #os.spawnlp(os.P_WAIT, './node_modules/.bin/ng', 'ng', 'build', '--configuration=stable', '--prod', '--extract-css')

    def create_sections(self, content):
        m = re.findall('(<h[2-3]>(.*)</h)', content)

        if m is None or len(m) == 0:
            return content

        for match in m:
            title = match[1].replace('/', ' ')
            replace = '<a class="dashAnchor" name="//apple_ref/Section/%s"></a>%s' % (quote(title), match[0])
            content = content.replace(match[0], replace)

        return content

    def build_guides(self):
        pattern = os.path.join(self.generated, 'generated', 'docs', 'guide', '**', '*.json')
        for guideJson in glob.glob(pattern, recursive=True):
            with open(guideJson, 'rt') as f:
                guide = json.load(f)
                self.create_folder(guide['id'])

                m = re.search(r'<h1>(.*)</h1>', guide['contents'])
                content = re.sub(r'href="/?(api/[a-zA-Z0-9-/]*)"', r'href="\1.html"', guide['contents'])
                content = re.sub(r'href="/?(guide/[a-zA-Z0-9-/]*)"', r'href="\1.html"', content)
                content = re.sub(r'href="/?(guide/[a-zA-Z0-9-/]*)(#.*)"', r'href="\1.html\2"', content)
                content = re.sub(r'href="(../class.*)"', r'href="javascript:;"', content)

                content = self.create_sections(content)

                title = (guide['id'].split('/')[-1]) if m is None else m.groups()[0]

                self.write_template(guide['id'], title, content)

        pass

    def build_misc(self):
        for miscJson in ['code-of-conduct', 'external-resources']:
            fileName = os.path.join(self.generated, 'generated', 'docs', miscJson + '.json')
            if not os.path.exists(fileName):
                continue

            with open(fileName, 'rt') as f:
                doc = json.load(f)

                if miscJson == 'external-resources':
                    doc['id'] = 'resources'
                else:
                    title = 'Code of Conduct'

                content = self.create_sections(doc['contents'])

                self.write_template(doc['id'], title, content)

    def build_api_index(self, index):
        content = '<h1 class="no-toc">API List</h1>\n<article class="api-list-container l-content-small docs-content"><div>'
        for i in index:
            rendered = self.api_list.render(name=i['title'], apis=i['items'])
            content += re.sub(r'href="(api/[a-zA-Z0-9-/]*)"', r'href="\1.html"', rendered) + '\n'
        content += '</div></article>'

        self.write_template('api/api-list', 'API List', content)

    def build_api(self):
        basePath = os.path.join(self.generated, 'generated', 'docs')
        pattern = os.path.join(basePath, 'api', '**/*.json')
        os.mkdir(os.path.join(self.output, 'api'))
        for apiJson in glob.glob(pattern, recursive=True):
            basename = os.path.basename(apiJson)
            with open(apiJson, 'rt') as f:
                api = json.load(f)

                if basename == 'api-list.json':
                    self.build_api_index(api)
                    continue

                self.create_folder(api['id'])

                content = re.sub(r'href="(api/[a-zA-Z0-9-/]*)', r'href="\1.html', api['contents'])
                content = re.sub(r'img src="/assets/(.*)"', r'img src="assets/\1"', content)
                content = content.replace('<a href="/api">', '<a href="api/api-list.html">')

                self.write_template(api['id'], api['title'], content)

    def build_dash_index(self):
        if os.path.isdir(os.path.join(self.cwd, 'rxjs.docset')):
            shutil.rmtree(os.path.join(self.cwd, 'rxjs.docset'))

        idx = os.path.join(self.cwd, 'rxjs.docset', 'Contents', 'Resources', 'docSet.dsidx')
        os.makedirs(os.path.dirname(idx))
        conn = sqlite3.connect(idx)
        c = conn.cursor()
        c.execute('''CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT)''')
        c.execute('''CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path)''')

        with open(os.path.join(self.generated, 'generated', 'navigation.json')) as f:
            navigation = json.load(f)
            for item in navigation['SideNav']:
                self.export_item(item, c)

        types = {'const': 'Constant', 'interface': 'Interface', 'class': 'Class', 'function': 'Function', 'type-alias': 'Type', 'enum': 'Enum'}
        with open(os.path.join(self.generated, 'generated', 'docs', 'api', 'api-list.json')) as f:
            api = json.load(f)
            for group in api:
                for item in group['items']:
                    if os.path.exists(os.path.join(self.output, item['path'] + '.html')):
                        c.execute("INSERT INTO searchIndex(name, type, path) VALUES ('%s', '%s', '%s')" % (item['title'], types[item['docType']], item['path'] + '.html'))

        c.close()
        conn.commit()
        conn.close()
        shutil.copytree(self.output, os.path.join(self.cwd, 'rxjs.docset', 'Contents', 'Resources/Documents'))
        shutil.copy(os.path.join(self.cwd, 'templates', 'Info.plist'), os.path.join(self.cwd, 'rxjs.docset', 'Contents'))
        shutil.copy(os.path.join(self.cwd, 'templates', 'icon.png'), os.path.join(self.cwd, 'rxjs.docset'))
        shutil.copy(os.path.join(self.cwd, 'templates', 'icon@2x.png'), os.path.join(self.cwd, 'rxjs.docset'))

    def export_item(self, item, cursor):
        if 'children' in item:
            for child in item['children']:
                self.export_item(child, cursor)

        if 'title' in item and 'url' in item:    
            if item['url'] in ['operator-decision-tree']:
                return
            if item['title'] == 'API':
                item['title'] = 'API List'
                item['url'] = 'api/api-list'

            if item['title'] == 'Reference':
                item['url'] = 'api/index'

            if os.path.exists(os.path.join(self.output, item['url'] + '.html')):
                cursor.execute("INSERT INTO searchIndex(name, type, path) VALUES ('%s', 'Guide', '%s')" % (item['title'], item['url'] + '.html'))

    def build(self):
        self.build_rxjs()
        self.clean_output()
        self.copy_stylesheet()
        self.build_guides()
        self.build_api()
        self.build_misc()
        self.build_dash_index()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: %s rxjs-dir' % sys.argv[0])
        exit(0)

    builder = Builder(sys.argv[1])

    builder.build()
