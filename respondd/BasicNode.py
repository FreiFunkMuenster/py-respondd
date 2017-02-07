import psutil
from .Cache import Cache
class BasicNode(object):

	def getAddrsOfIface(self, ifName):
		ifaces = Cache.getGlobal('ifaces_addrs', BasicNode.updateNetIfAddrs)
		if ifName in ifaces:
			return ifaces[ifName]
		return []

	@staticmethod
	def updateNetIfAddrs():
		return psutil.net_if_addrs()

	def getMacAddr(self):
		return Cache.getLocal('iface_mac', self.domain['site_code'], self.updateMacAddr)

	def updateMacAddr(self):
		addrs = self.getAddrsOfIface(self.domain['bat_iface'])
		for a in addrs:
			if a.family == 17:
				return a.address
