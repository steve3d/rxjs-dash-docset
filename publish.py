#!/usr/bin/env python3

import os, json, shutil, glob, sys
import os.path as path

class Publish:
    def __init__(self, lib):
        self.name = 'RxJS'
        with open(path.join(path.realpath(lib), 'docs_app', 'dist', 'generated', 'navigation.json'), 'rt') as f:
            navigation = json.load(f)
            self.version = navigation['__versionInfo']['raw']
        self.cwd = os.getcwd()
        self.destDir = path.realpath(path.join(path.dirname(sys.argv[0]), '..', 'Dash-User-Contributions', 'docsets', 'RxJS'))
        if not path.isdir(path.join(self.cwd, 'rxjs.docset')):
            raise Exception('Docset does not exist, please build first.')

        if not path.isdir(self.destDir):
            raise Exception('Parent folder does not have Dash-User-Contributions repo.')


    def getVersion(self):
        ver = dict()
        ver['version'] = self.version
        ver['archive'] = 'versions/{}/{}'.format(self.version, self.name + '.tgz')
        return ver        

    def updateVersions(self):        
        if path.isfile(path.join(self.destDir, 'docset.json')):
            with open(path.join(self.destDir, 'docset.json')) as f:
                versions = json.load(f)
        else: 
            with open(path.join(self.cwd, 'templates', 'docset.json')) as f:
                versions = json.load(f)

        versions['name'] = self.name
        versions['author']['name'] = 'Steve Yin'
        versions['author']['link'] = 'https://gitlab.com/steve3d/rxjs-dash-docset'

        if 'specific_versions' not in versions:
            versions['specific_versions'] = []
        
        if len(versions['specific_versions']) == 0:
            versions['version'] = self.version

        if self.version.count('.') == 1:
            minorVersion = self.version
        else:
            minorVersion = self.version[0:self.version.rfind('.')]
        
        filtered = list(filter(lambda x: not x['version'].startswith(minorVersion), versions['specific_versions']))
        filtered.append(self.getVersion())
        filtered.sort(key=lambda x: x['version'], reverse = True)

        versions['specific_versions'] = filtered

        os.spawnlp(os.P_WAIT, 'tar', 'tar', '--exclude=".DS_Store"', '-czf', self.name + '.tgz', self.name + '.docset')

        latest = versions['specific_versions'][0]

        if latest['version'] >= versions['version']:
            versions['version'] = latest['version']
            shutil.copy2(path.join(self.cwd, self.name + '.tgz'), self.destDir)
        
        with open(path.join(self.destDir, 'docset.json'), 'wt') as f:
            f.write(json.dumps(versions, indent = 4))

        self.cleanVersions(versions['specific_versions'])

    def cleanVersions(self, versions):
        existing = list(map(lambda x: x['version'], versions))
        for item in glob.glob(path.join(self.destDir, 'versions', '*')):        
            ver = item[item.rfind('/') + 1:]
            if ver in existing:
                continue
            else:
                print('Deleting unneeded version: ' + ver)
                shutil.rmtree(item)
    
    def publish(self):
        versionRoot = path.join(self.destDir, 'versions', self.version)
        os.makedirs(versionRoot, 0o755, True)
        shutil.copy2(path.join(self.cwd, 'templates', 'icon.png'), self.destDir)
        shutil.copy2(path.join(self.cwd, 'templates',  'icon@2x.png'), self.destDir)
        self.updateVersions()
        print('Publish {}-{} to {} done.'.format(self.name, self.version, self.destDir))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: %s rxjs-dir' % sys.argv[0])
        exit(0)

    pub = Publish(sys.argv[1])

    pub.publish()