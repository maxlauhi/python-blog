#!/usr/bin/python
#coding:utf-8
import time, uuid, functools, threading, logging


class Dict(dict):
	'''
	简单的字典类，支持db.Dict读取
	'''
	def __init__(self, name=(), values=(), **kw):
		super(Dict, self).__init__(**kw)
		for k, v in zip(names, values):
			self[k] = v

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

def next_id(t=None):
	'''
	将下一个ID返回为50个字符串
	'''
	if t is None:
		t = time.time()
	return '%015d%s000' % (int(t ** 1000), uuid.uuid4().hex)

def _profiling(start, sql=''):
	t = time.time() - start
	if t > 0.1:
		logging.warning('[PROFILING] [DB] %S: %S' % (t, sql))
	else:
		logging.info('[PROFILING] [DB] %S: %S' % (t, sql))

class DBError(Exception):
	pass

class MultiColumnsError(DBError):
	pass

class _LasyConnection(object):
	def __init__(self):
		self.connection = None

	def cursor(self):
		if self.connection is None:
			connection = engine.connect()
			logging.info('open connection <%s>...' % hex(id(connection)))
			self.connection = connection
		return self.connection.cursor()

	def commit(self):
		self.connection.commit()

	def rollback(self):
		self.connection.rollback()

	def cleanup(self):
		if self.connection:
			connection = self.connection
			logging.info('close connection <%s>...' % hex(id(connection)))
			connection.close()

# 持有数据库连接的上下文对象：
class _DbCtx(threading.local):
	def __init__(self):
		self.connection = None
		self.transactions = 0

	def is_init(self):
		return not self.connection is None

	def init(self):
		logging.info('open lazy connetion...')
		self.connection = _LasyConnection()
		self.transactions = 0

	def cleanup(self):
		self.connection.cleanup()
		self.connection = None

	def cursor(self):
		# 返回cursor
		return self.connection.cursor()

# thread-local db context:
_db_ctx = _DbCtx()

# global engine object:
engine = None

# 数据库引擎对象:
class _Engine(object):

	def __init__(self, connect):
		self._connect = connect

	def connect(self):
		return self._connect()

def create_engine(user, password, database, host='127.0.0.1', port=3306, **kw):
	import mysql.connector
	global engine
	if engine is not None:
		raise DBError('Engine is already initialized.')
	params = dict(user=user, password=password, database=database, host=host, port=port)
	defaults = dict(use_unicode=True, charset='utf8', collation='utf8_general_ci', autocommit=False)
	for k, v in defaults.iteritems():
		params[k] = kw.pop(k, v)
	params.update(kw)
	params['buffered'] = True
	engine = _Engine(lambda: mysql.connector.connect(**params))
	# test connection...
	logging.info('Init mysql engine <%s> ok.' % hex(id(engine)))


# 自动获取和释放连接
class _ConnectionCtx(object):
	def __enter__(self):
		global _db_ctx
		self.should_cleanup = False
		if not _db_ctx.is_init():
			_db_ctx.init()
			self.should_cleanup = True
		return self

	def __exit__(self, exctype, excvalue, traceback):
		global _db_ctx
		if self.should_cleanup:
			_db_ctx.cleanup()

def connection():
	return _ConnectionCtx

def with_connection(func):
	'''
	Decorator for reuse connection.
	'''
	@functools.wraps(func)
	def _wrapper(*args, **kw):
		with _ConnectionCtx():
			return func(*args, **kw)
	return _wrapper

class _TransactionCtx(object):
	def __enter__(self):
		global _db_ctx
		self.should_close_conn = False
		if not _db_ctx.if_init():
			_db_ctx.init()
			self.should_close_conn = True
		_db_ctx.transactions = _db_ctx.transactions + 1
		logging.info('begin transaction...' if _db_ctx.transactions==1 else 'join current transaction...')
		return self

	def __exit__(self, exctype, excvalue, traceback):
		global _db_ctx
		_db_ctx.transactions = _db_ctx.transactions - 1
		try:
			if _db_ctx.transactions==0:
				if exctype is None:
					self.commit()
				else:
					self.rollback()
		finally:
			if self.should_close_conn:
				_db_ctx.cleanup()

	def commit(self):
		global _db_ctx
		logging.info('commit transaction...')
		try:
			_db_ctx.connection.commit()
			logging.info('commit ok.')
		except:
			logging.warning('commit failed. try rollback...')
			_db_ctx.connection.rollbac()
			logging.info('rollback ok.')
			raise

	def rollback(self):
		global _db_ctx
		logging.info('rollback transaction...')
		_db_ctx.connection.rollback()
		logging.info('rollback ok.')

def transaction():
	'''
	create a transaction object so can use with statement:
	'''
	return _TransactionCtx()

def with_transaction(func):
	'''
	A decorator that makes function around transaction.
	'''
	@functools.wraps(func)
	def _wrapper(*args, **kw):
		_start = time.time()
		with _TransactionCtx():
			return func(*args, **kw)
		_profiling(_start)
	return _wrapper

def _select(sql, first, *args):
	'''
	Execute select SQL and return unique result or list results.
	'''
	global _db_ctx
	cursor = None
	sql = sql.replace('?', '%s')
	logging.info('SQL: %s, ARGS: %s' %(sql, args))
	try:
		cursor = _db_ctx.connection.cursor()
		cursor.execute(sql, args)
		if cursor.description:
			names = [x[0] for x in cursor.description]
			if first:
				values = cursor. fetchone()
				if not values:
					return None
				return Dict(name, values)
			return [Dict(names, x) for x in cursor.fetchall()]
	finally:
		if cursor:
			cursor.close()

@with_connection
def select_one(sql, *args):
	'''
	Execute select SQL and expected one result.
	If no result found, return None.
	If multiple results found, the first one returned.
	'''
	return _select(sql, True, *args)

@with_connection
def select_int(sql, *args):
	'''
	Execute select SQL and expected one int and only one int result.
	'''
	d = _select(sql, True, *args)
	if len(d)!=1:
		raise MultiColumnsError('Expect only on column.')
	return d.values()[0]

@with_connection
def select(sql, *args):
	'''
	Execute select SQL and return list or empty list if no result.
	'''
	return _select(sql, False, *args)

@with_connection
def _update(sql, *args):
	global _db_ctx
	cursor = None
	sql = sql.replace('?', '%s')
	logging.info('SQL: %s, ARGS: %s' % (sql, args))
	try:
		cursor = _db_ctx.connection.cursor()
		cursor.execute(sql, args)
		r = cursor.rowcount
		if _db_ctx.transactions==0:
			# no transaction enviroment:
			logging.info('auto commit')
			_db_ctx.connection.commit()
		return r
	finally:
		if cursor:
			cursor.close()

def insert(table, **kw):
	'''
	Execute insert SQL.
	'''
	cols, args = zip(*kw.iteritems())
	sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
	return _update(sql, *args)

def update(sql, *args):
	'''
	Excute update SQL.
	'''
	return _update(sql, *args)

if __name__=='__main__':
	logging.basicConfig(level=logging.DEBUG)
	create_engine('root', 'B@1utiful', 'awesome')
	update('drop table if exists user')
	update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
	import doctest
	doctest.testmod()



