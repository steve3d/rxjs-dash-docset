# RxJS Docset Generator for dash

This script creates a API docset for RxJS from its documentation.
The docset can be used in the incredibly useful [Dash](https://kapeli.com/dash).
It is submitted also as a [User Contributed docset](https://github.com/Kapeli/Dash-User-Contributions) for Dash.

## Install

Requires `npm`, `git`, `Python > 3.6.x`, `Jinja2`


## Build Docset
- create some folder like `dash-doc`
- checkout this repo under `dash-doc`
- checkout rxjs repo under `dash-doc`
- `cd dash-doc/rxjs/docs_app`
- `git checkout 6.3.3` or any version you want to build
- `npm run setup`
- `npm run build`
- `cd dash-doc/rxjs-dash-docset`
- `pip3 install -r requirements.txt`
- `./build.py ../rxjs`


then wait for some time, you will get a rxjs docset for [Dash](https://kapeli.com/dash)