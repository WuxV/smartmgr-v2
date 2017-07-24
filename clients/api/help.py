# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys, os, json
from flask import Flask, abort, make_response, request, render_template
from flask_frozen import Freezer

from api_doc import api_items, enum_items, struct_items

app = Flask(__name__)
freezer = Freezer(app)

reload(sys)
sys.setdefaultencoding( "utf-8" )

# 获取帮助页面
@app.route('/help.html', methods=['GET'])
def help():
    titles = []
    i = 0
    group = {}
    for item in api_items:
        if item['type'] not in group.keys():
            i += 1
            group[item['type']] = {}
            group[item['type']]['index']     = i
            group[item['type']]['name']      = item['type']
            group[item['type']]['sub_titles'] = []
        sub_title = {}
        sub_title['index'] = len(group[item['type']]['sub_titles']) + 1
        sub_title['info']  = item
        sub_title['info']['url'] = sub_title['info']['url'].replace("<", "&lt;")
        sub_title['info']['url'] = sub_title['info']['url'].replace(">", "&gt;")
        group[item['type']]['sub_titles'].append(sub_title)
    titles = sorted(group.values(), key=lambda asd:asd['index'])
    return render_template("help.tpl", titles=titles, struct_items=struct_items, enum_items=enum_items)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(host="0.0.0.0", port=9000)
