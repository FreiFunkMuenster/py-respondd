import netifaces
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
		print(args)
		return netifaces.ifaddresses(args[0])

	def getMacAddr(self):
		return Cache.getLocal('iface_mac', self.domain['site_code'], self.updateMacAddr)

	def updateMacAddr(self, *args):
		return self.getAddrsOfIface(self.domain['bat_iface'])[netifaces.AF_LINK][0]['addr']
