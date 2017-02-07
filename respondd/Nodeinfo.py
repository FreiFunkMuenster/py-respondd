import glob, socket, psutil
from .Cache import Cache
from .BasicNode import BasicNode
class Nodeinfo(BasicNode):
	def __init__(self, domain):
		self.domain = domain

	def get(self):
		cpuCount, cpuType = self.cpuInfo()
		nodeInfo = {
			'software': {
				'autoupdater': {
					'enabled': False
				},
				'batman-adv': {
					'version': open('/sys/module/batman_adv/version', 'r').read()[:-1]
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
						'interfaces': {
							'tunnel': self.getTunnMacAddrs(),
							'other': [self.getMacAddr()]
						}
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

	def getHostname(self):
		return Cache.getGlobal('hostname', Nodeinfo.updateHostname)
		
	@staticmethod
	def updateHostname():
		return socket.gethostname()

	def getProcessList(self):
		return Cache.getGlobal('process_list', Nodeinfo.updateProcessList)

	@staticmethod
	def updateProcessList():
		return [[p.name(),p.cmdline()] for p in Cache.getGlobal('process_iter', Nodeinfo.updateProcessIter)]

	def isProcessRunning(self, processName, processArg = None):
		for p in self.getProcessList():
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

	def updateV6Addrs(self):
		addrs = self.getAddrsOfIface(self.domain['bat_iface'])
		v6addrs = []
		for a in addrs:
			if a.family == 10:
				v6addrs.append(a.address.split('%')[0])
		return v6addrs

	def cpuInfo(self):
		return Cache.getGlobal('cpu_info', Nodeinfo.updateCpuInfo)

	@staticmethod
	def updateCpuInfo():
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
		return Cache.getLocal('tun_mac_addr', self.domain['site_code'], self.updateV6Addrs)

	def updateTunnMacAddrs(self):
		macs = []
		fl = glob.glob('/sys/class/net/'+self.domain['bat_iface']+'/lower_*/address')
		for fe in fl:
			macs.append(open(fe, 'r').read()[:-1])
		return macs

	@staticmethod
	def updateProcessIter():
		return psutil.process_iter()
