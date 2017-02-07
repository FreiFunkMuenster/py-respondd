import time

class Cache(object):
	globalCache = {}
	localCace = {}
	timeout = 0
	now = time.time()

	@staticmethod
	def setTimeout(timeout):
		Cache.timeout = timeout

	@staticmethod
	def updateTime():
		Cache.now = time.time()

	@staticmethod
	def _isValid(timestamp):
		return True if Cache.now - Cache.timeout <= timestamp else False

	@staticmethod
	def getGlobal(kw, fx, args = ()):
		if kw not in Cache.globalCache:
			Cache.globalCache[kw] = {
				'timestamp': Cache.now,
				'value' : fx(args),
				'args' : args
			}
		elif not Cache._isValid(Cache.globalCache[kw]['timestamp']):
			Cache.globalCache[kw]['value'] = fx(args)
		#else:
		#	print("Cache used! [global, "+kw+']')

		return Cache.globalCache[kw]['value']

	@staticmethod
	def getGlobalB(kw, fx, args = ()):
		return fx()

	@staticmethod
	def getLocal(kw, dom, fx, args = ()):
		if dom not in Cache.localCace:
			Cache.localCace[dom] = {}
		if kw not in Cache.localCace[dom]:
			Cache.localCace[dom][kw] = {
				'timestamp': Cache.now,
				'value' : fx(args),
				'args' : args
			}
		elif not Cache._isValid(Cache.localCace[dom][kw]['timestamp']):
			Cache.localCace[dom][kw]['value'] = fx(args)
		#else:
		#	print("Cache used! [local, "+kw+','+dom+']')

		return Cache.localCace[dom][kw]['value']

	@staticmethod
	def getLocalB(kw, dom, fx, args = ()):
		return fx()