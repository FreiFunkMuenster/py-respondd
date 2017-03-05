import netifaces, psutil
from .Cache import Cache
class BasicNode(object):

	def getBatmanVersion(self):
		return Cache.getGlobal('batman_version', BasicNode.updateBatmanVersion)

	@staticmethod
	def updateBatmanVersion(*args):
		return open('/sys/module/batman_adv/version', 'r').read()[:-1]

	def getAddrsOfIface(self, ifName):
		return Cache.getGlobal('ifaces_addrs_' + ifName, BasicNode.updateNetIfAddrs, ifName)

	@staticmethod
	def updateNetIfAddrs(*args):
		return netifaces.ifaddresses(args[0])

	def getMacAddr(self):
		return Cache.getLocal('iface_mac', self.domain['site_code'], self.updateMacAddr)

	def updateMacAddr(self, *args):
		if 'br_iface' in self.domain and self.domain['br_iface'] != False:
			idIf = self.domain['br_iface']
		else:
			idIf = self.domain['bat_iface']
		return self.getAddrsOfIface(idIf)[netifaces.AF_LINK][0]['addr']

	@staticmethod
	def getProcessList():
		return Cache.getGlobal('process_list', BasicNode.updateProcessList)

	@staticmethod
	def updateProcessList(args):
		res = []
		for p in psutil.process_iter():
			try:
				with p.oneshot():
					res.append([p.name(), p.cmdline(), p.status()])
			except psutil.NoSuchProcess as err:
				print(err)
		return res