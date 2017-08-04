# -*- coding: utf-8 -*-

class Model(dict):
	__metaclass__ = ModelMetaclass

	def __init__(self, **kw):
	    super(Model, self).__init__(**kw)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

	def __setattr__(self, key, value):
		self[key] = value

class ModelMetaclass(type):
	def __new__(cls, name, bases, attrs):
		mapping = ...
		primary_key = ...
		__table__ = cls.__table__
        # 
		attrs['__mapping__'] = mapping
		attrs['__primary_key__'] = __primary_key__
		attrs['__table__'] = __table__
		return type.__new__(cls, name, bases, attrs)
