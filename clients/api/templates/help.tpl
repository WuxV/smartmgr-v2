<!DOCTYPE html> 
<HTML>
<HEAD>
        <META http-equiv="Content-Type" content="text/html; charset=utf-8">
        <LINK rel="Stylesheet" type="text/css" href="/static/main.css" />
        <TITLE>PBData smartmgr API</TITLE>
</HEAD>
<BODY>
<div class=main>
<h1  class=header>PBData smartmgr API (v1.0)</h1>
<div class=menu></div>
<div class=page>
    <!-- 目录 start -->
    <div class=top_ul>
    一. 接口清单
    <ul>
        {% for title in titles -%}
        <li>
            {{title.index}}. {{title.name}}
            <ul>
                {% for sub_title in title.sub_titles -%}
                <li><a href="#{{sub_title.info.href}}">{{title.index}}.{{sub_title.index}} {{sub_title.info.title}}</a></li>
                {% endfor %}
            </ul>
        </li>
        {% endfor %}
    </ul>
    二. 附表
    <ul>
        <li>
            1. 基本数据结构
            <ul>
                {% for struct_item in struct_items -%}
                <li><a href="#{{struct_item.type}}">{{struct_item.type}}</a></li>
                {% endfor %}
                {% for enum_item in enum_items -%}
                <li><a href="#{{enum_item.type}}">(enum){{enum_item.type}}</a></li>
                {% endfor %}
            </ul>
        </li>
    </ul>
    </div>
    <!-- 目录 end -->
    <div class=sub>一. 接口清单</div>
    <!-- 接口 start -->
    {% for title in titles -%}
    <div class=sub>{{title.index}} {{title.name}}</div>
    {% for sub_title in title.sub_titles -%}
    <!-- sub_topic start -->
    <div class=sub_topic>
        <div class=topic_title><a name="{{sub_title.info.href}}">{{title.index}}.{{sub_title.index}} {{sub_title.info.title}}</a></div>
        <div class=topic_key>角色和平台:</div>
            <table border="1" cellpadding="0" cellspacing="0" class=attr>
                <tr>
                    <th width="50%">角色</th>
                    <th>平台</th>
                </tr>
                <tr>
                    <td align=center>{{', '.join(sub_title.info.role)}}</td>
                    <td align=center>{{', '.join(sub_title.info.platform)}}</td>
                </tr>
            </table>
        <div class=topic_key>请求地址:</div>
        <div class=topic_url>{{sub_title.info.url}}</div>
        <div class=topic_key>请求参数:</div>
        <div class=topic_request_attr>
            {% if sub_title.info.req_attr|length != 0 %}
            <table border="1" cellpadding="0" cellspacing="0" class=attr>
                <tr>
                    <th width="25%">名称</th>
                    <th width="20%">类型</th>
                    <th width="10%">是否必须</th>
                    <th>描述</th>
                </tr>
                {% for attr in sub_title.info.req_attr%}
                <tr>
                    <td>{{attr.name}}</td>
                    <td>
                    {% if attr.type not in ["(array)string", "string", "uint32", "int32", "uint64", "bool", "float", "double"] %}
                        <a href="#{{attr.type}}">{{attr.type}}</a>
                    {%else%}
                        {{attr.type}}
                    {%endif%}
                    </td>
                    <td align=center>
                    {% if attr.must %}
                        是
                    {%else%}
                        否
                    {%endif%}
                    </td>
                    <td>{{attr.info}}</td>
                </tr>
                {% endfor %}
            </table>
            {%else%}
                无
            {%endif%}
        </div>
        <div class=topic_key>响应参数:</div>
        <div class=topic_response_attr>
            <table border="1" cellpadding="0" cellspacing="0" class=attr>
                <tr>
                    <th width="25%">名称</th>
                    <th width="20%">类型</th>
                    <th width="10%">是否必须</th>
                    <th>描述</th>
                </tr>
                <tr>
                    <td>rc</td>
                    <td><a href="#ResponseCode">ResponseCode</a></td>
                    <td align=center>是</td>
                    <td>业务逻辑请求返回状态</td>
                </tr>
                <tr>
                    <td>head</td>
                    <td><a href="#Head">Head</a></td>
                    <td align=center>是</td>
                    <td>业务逻辑请求返回头部</td>
                </tr>
                {% for attr in sub_title.info.res_attr%}
                <tr>
                    <td>{{attr.name}}</td>
                    <td><a href="#{{attr.type}}">{{attr.type}}</a></td>
                    <td align=center>
                    {% if attr.must %}
                        是
                    {%else%}
                        否
                    {%endif%}
                    </td>
                    <td>{{attr.info}}</td>
                </tr>
                {% endfor %}
            </table>
            {% if sub_title.info.res_attr|length != 0 %}
            <a name="{{sub_title.info.res_attr[0].type}}">{{sub_title.info.res_attr[0].type}}:</a>
            <table border="1" cellpadding="0" cellspacing="0" class=attr>
                <tr>
                    <th width="25%">名称</th>
                    <th width="20%">类型</th>
                    <th width="10%">是否必须</th>
                    <th>描述</th>
                </tr>
                {% for attr in sub_title.info.response%}
                <tr>
                    <td>{{attr.name}}</td>
                    <td>
                    {% if attr.type not in ["(array)string", "string", "uint32", "int32", "uint64", "bool", "float", "double"] %}
                        <a href="#{{attr.type}}">{{attr.type}}</a>
                    {%else%}
                        {{attr.type}}
                    {%endif%}
                    </td>
                    <td align=center>
                    {% if attr.must %}
                        是
                    {%else%}
                        否
                    {%endif%}
                    </td>
                    <td>{{attr.info}}</td>
                </tr>
                {% endfor %}
            </table>
            {% endif %}
        </div>
        <div class=topic_key>请求示例:</div>
        <div class=topic_request_demo>
            <pre>{{sub_title.info.req_demo}}</pre>
        </div>
        <div class=topic_key>响应示例:</div>
        <div class=topic_response_demo>
        <pre>{{sub_title.info.res_demo}}</pre>
        </div>
    </div>
    <!-- sub_topic end -->
    {% endfor %}
    {% endfor %}
    <!-- 接口 end -->
    <!-- 基本数据结构 start -->
    <div class=sub>二. 基本数据结构</div>
    {% for struct_item in struct_items -%}
    <!-- sub_topic start -->
    <div class=sub_topic>
        <div class=topic_title><a name="{{struct_item.type}}">{{struct_item.type}}</a></div>
        <div class=topic_response_attr>
            <table border="1" cellpadding="0" cellspacing="0" class=attr>
                <tr>
                    <th width="25%">名称</th>
                    <th width="20%">类型</th>
                    <th width="10%">是否必须</th>
                    <th>描述</th>
                </tr>
                {% for attr in struct_item.attr%}
                <tr>
                    <td>{{attr.name}}</td>
                    <td>
                    {% if attr.type not in ["(array)string", "string", "uint32", "int32", "uint64", "bool", "float", "double"] %}
                        <a href="#{{attr.type}}">{{attr.type}}</a>
                    {%else%}
                        {{attr.type}}
                    {%endif%}
                    </td>
                    <td align=center>
                    {% if attr.must %}
                        是
                    {%else%}
                        否
                    {%endif%}
                    </td>
                    <td>{{attr.info}}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
    <!-- sub_topic end -->
    {% endfor %}
    {% for enum_item in enum_items -%}
    <!-- sub_topic start -->
    <div class=sub_topic>
        <div class=topic_title><a name="{{enum_item.type}}">(enum){{enum_item.type}}</a></div>
        <div class=topic_response_attr>
            <table border="1" cellpadding="0" cellspacing="0" class=attr>
                <tr>
                    <th width="30%">名称</th>
                    <th width="5%">值</th>
                    <th>描述</th>
                </tr>
                {% for attr in enum_item.attr%}
                <tr>
                    <td>{{attr.name}}</td>
                    <td align=center>{{attr.valu}}</td>
                    <td>{{attr.info}}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
    <!-- sub_topic end -->
    {% endfor %}
    <!-- 接口 end -->
</div>
</BODY>
</HTML>
