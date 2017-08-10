# -*- coding: utf-8 -*-

from models import User, Blog, Comment

from transwarp import db

db.create_engine(user='www-data', password='www-data', database='awesome')

u = User(name='test', email='z04jr128@qq.com', password='O3to2@r', image='about:blank')

u.insert()

print 'new user id:', u.id

u1 = User.find_first('where email=?', 'z04jr128@qq.com')
print 'find user\'s name:', u1.name

u1.delete()

u2 = User.find_first('where email=?', 'z04jr128@qq.com')
print 'find user:', u2