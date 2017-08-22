# -*- coding: utf-8 -*-

# transwarp/web.py

# 首页：
@get('/')
def index():
	return '<h1>Index page</h1>'
