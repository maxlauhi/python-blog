# -*- coding: utf-8 -*-

'''
Models of user, blog and comment.
'''

import time, uuid

from transwarp.db import next_id
from transwarp.orm import Model, StringField, BooleanField, FloatField, TextField

class User(Model):
	__table__ = 'users'

	id = StringField(primary_key=True, ddl='varchar(50)')
	name = StringField(ddl='varchar(50)')
'''
	email = StringField(updatable=False, ddl='varchar(50)')
	password = StringField(ddl='varchar(50)')
	admin = BooleanField()
	image = StringField(ddl='varchar(500)')
	created_at = FloatField(updatable=False, default=time.time)

class Blog(Model):
	__table__ = 'blogs'

	id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
	user_id = StringField(updatable=False, ddl='varchar(50)')
	user_name = StringField(ddl='varchar(50)')
	user_image = StringField(ddl='varchar(50)')
	summary = StringField(ddl='varchar(200)')
	content = Textfield()
	created_at = FloatField(updatable=False, default=time.time)

class Comment(Model):
	__table__ = 'comments'

	id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
	blog_id = StringField(updatable=False, ddl='varchar(50)')
	user_id = StringField(updatable=False, ddl='varchar(50)')
	user_image = StringField(ddl='varchar(50)')
	content = TextField()
	created_at = FloatField(updatable=Flase, default=time.time)
'''