import glob, socket, re, netifaces
from .Cache import Cache
from .BasicNode import BasicNode
class Nodeinfo(BasicNode):
	def __init__(self, domainData, globalData):
		self.domain = domainData
		self.globalData = globalData
		self.interfaceTypeRegexPatterns = None
		if 'interface_type_regex_patterns' in self.globalData:
			self.interfaceTypeRegexPatterns = self.prepareInterfaceRegex(self.globalData['interface_type_regex_patterns'])

	def get(self):
		cpuCount, cpuType = self.cpuInfo()
		nodeInfo = {
			'software': {
				'autoupdater': {
					'enabled': False
				},
				'batman-adv': {
					'version': self.getBatmanVersion()
				},
				'fastd': {
					'enabled': self.isProcessRunning('fastd')
				},
				'tunneldigger': {
					'enabled': self.isProcessRunning('python','l2tp_broker')
				}
			},
			'node_id' : self.getMacAddr().replace(':',''),
			'owner' : {
				'contact' : 'mail@simon-wuellhorst.de'
			},
			'network': {
				'addresses': self.getV6Addrs(),
				'mesh': {
					self.domain['bat_iface'] : {
						'interfaces': self.getInterfaceMacs()
					}
				},
				'mac': self.getMacAddr()
			},
			'system': {
				'site_code': self.domain['site_code']
			},
			'hostname': self.getHostname() + '_' + self.domain['site_code'],
			'hardware': {
				'model': cpuType,
				'nproc': cpuCount
			}
		}
		return nodeInfo

	def prepareInterfaceRegex(self,config):
		res = {}
		for k,v in config.items():
			res[k] = re.compile(v)
		return res

	def getHostname(self):
		return Cache.getGlobal('hostname', Nodeinfo.updateHostname)
		
	@staticmethod
	def updateHostname(args):
		return socket.gethostname()

	def isProcessRunning(self, processName, processArg = None):
		for p in BasicNode.getProcessList():
			if p[0] == processName:
				if processArg == None:
					return True
				if len(p) == 1:
					continue
				for arg in p[1]:
					if processArg in arg:
						return True
		return False

	def getV6Addrs(self):
		return Cache.getLocal('iface_v6', self.domain['site_code'], self.updateV6Addrs)

	def updateV6Addrs(self, *args):
		addrs = self.getAddrsOfIface(self.domain['bat_iface'])[netifaces.AF_INET6]
		return [x['addr'] for x in addrs]

	def cpuInfo(self):
		return Cache.getGlobal('cpu_info', Nodeinfo.updateCpuInfo)

	@staticmethod
	def updateCpuInfo(*args):
		with open('/proc/cpuinfo', 'r') as f:
			cpuinfo = f.readlines()
		cpuType = None
		cpuCount = 0
		for line in cpuinfo:
			if line.startswith('model name'):
				if cpuType == None:
					cpuType = line.split(': ')[1][:-1]
				cpuCount += 1
		return (cpuCount, cpuType)

	def getTunnMacAddrs(self):
		return Cache.getLocal('tun_mac_addr', self.domain['site_code'], self.updateTunnMacAddrs)

	def updateTunnMacAddrs(self, *args):
		macs = []
		fl = glob.glob('/sys/class/net/'+self.domain['bat_iface']+'/lower_*/address')
		for fe in fl:
			macs.append([fe.split('lower_')[1].split('/')[0],open(fe, 'r').read()[:-1]])
		return macs

	def getInterfaceMacs(self):
		return Cache.getLocal('iface_mac_addr', self.domain['site_code'], self.updateInterfaceMacs)

	def updateInterfaceMacs(self, *args):
		ifaces = self.getTunnMacAddrs()

		res = {
			'other': [self.getMacAddr()]
		}
		if self.interfaceTypeRegexPatterns != None:
			for iface in ifaces:
				for k,v in self.interfaceTypeRegexPatterns.items():
					if v.search(iface[0]) is not None:
						if k not in res:
							res[k] = [iface[1]]
						else:
							res[k].append(iface[1])
						break
				else:
					if k not in res:
						res['tunnel'] = [iface[1]]
					else:
						res['tunnel'].append(iface[1])
		else:
			res['tunnel'] = [x[1] for x in ifaces]


		return res