import socket, struct, array, fcntl, os, psutil
from .Cache import Cache
from .BasicNode import BasicNode

class Statistics(BasicNode):

	# from uapi/linux/sockios.h
	SIOCETHTOOL			= 0x8946 # /* Ethtool interface */

	# from linux/ethtool.h
	ETH_SS_STATS		= 1
	ETH_GSTRING_LEN		= 32
	ETHTOOL_GSSET_INFO	= 0x00000037 # /* Get string set info */
	ETHTOOL_GSTRINGS	= 0x0000001b # /* get specified string set */
	ETHTOOL_GSTATS		= 0x0000001d # /* get NIC-specific statistics */

	def __init__(self, domain):
		self.domain = domain
		self.n_stats, self.n_strings = self.prepareBatNeigh()

	def get(self):
		mem = self.getMemStats()
		total, running = self.getProcessCounts()
		batStats = Cache.getLocal('bat_neigh', self.domain['site_code'], self.updateBatNeigh)
		return {
			'traffic': {
				'forward': {
					'packets': batStats['forward'],
					'bytes': batStats['forward_bytes']
				},
				'tx': {
					'bytes': batStats['tx_bytes'],
					'packets': batStats['tx'],
					'dropped': batStats['tx_dropped']
				},
				'mgmt_rx': {
					'packets': batStats['mgmt_rx'],
					'bytes': batStats['mgmt_rx_bytes']
				},
				'rx': {
					'packets': batStats['rx'],
					'bytes': batStats['rx_bytes']
				},
				'mgmt_tx': {
					'packets': batStats['mgmt_tx'],
					'bytes': batStats['mgmt_tx_bytes']
				}
			},
			'memory': {
				'buffers' : mem.buffers,
				'total': mem.total,
				'free': mem.free,
				'cached' : mem.cached
			},
			'uptime': int(Cache.now-self.getBootTime()),
			'loadavg': os.getloadavg()[0],
			'processes': {
				'running': running,
				'total': total,
			},
			'node_id' : self.getMacAddr().replace(':','')
		}

	def prepareBatNeigh(self):
		fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

		sset_info = struct.pack('IIQI',Statistics.ETHTOOL_GSSET_INFO,0,2,0)# fixme: use correct variable instead 2
		sset_info_arr = array.array('B',sset_info)
		ifreq = struct.pack('16sP', str.encode(self.domain['bat_iface']), sset_info_arr.buffer_info()[0])
		fcntl.ioctl(fd, Statistics.SIOCETHTOOL, ifreq)
		n_stats = sset_info_arr[16]

		strings = struct.pack('III'+str(n_stats*Statistics.ETH_GSTRING_LEN)+'s',Statistics.ETHTOOL_GSTRINGS,Statistics.ETH_SS_STATS,n_stats,b'')
		strings_arr = array.array('B',strings)
		ifreq = struct.pack('16sP', str.encode(self.domain['bat_iface']), strings_arr.buffer_info()[0])
		fcntl.ioctl(fd, Statistics.SIOCETHTOOL, ifreq)
		res = struct.unpack('III'+str(n_stats*Statistics.ETH_GSTRING_LEN)+'s',strings_arr.tostring())[3]
		strings = []
		for line in range(n_stats):
			strings.append(str(res[line*Statistics.ETH_GSTRING_LEN:(line+1)*Statistics.ETH_GSTRING_LEN], 'utf-8').rstrip('\x00'))
		fd.close()
		return n_stats, strings

	def updateBatNeigh(self, *args):
		fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
		stats = struct.pack('IIQ'+str(self.n_stats*8)+'s',Statistics.ETHTOOL_GSTATS,self.n_stats,0,b'') #fixme: use Q instead 8*s
		stats_arr = array.array('B',stats)
		ifreq = struct.pack('16sP', str.encode(self.domain['bat_iface']), stats_arr.buffer_info()[0])
		fcntl.ioctl(fd, Statistics.SIOCETHTOOL, ifreq)
		res = struct.unpack('IIQ'+str(self.n_stats)+'Q',stats_arr.tostring())[2:]
		fd.close()
		return dict(zip(self.n_strings,res))

	def getMemStats(self):
		return Cache.getGlobal('mem_stats', self.updateMemStats)

	@staticmethod
	def updateMemStats(*args):
		return psutil.virtual_memory()

	def getBootTime(self):
		return Cache.getGlobal('boot_time', Statistics.updateBootTime)

	@staticmethod
	def updateBootTime(*args):
		return psutil.boot_time()

	def getProcessCounts(self):
		return Cache.getGlobal('process_counts', Statistics.updateProcessCounts)

	@staticmethod
	def updateProcessCounts(*args):
		total = 0
		running = 0
		for p in psutil.process_iter():
			total += 1
			if p.is_running() == True and p.status() == 'running':
				running += 1
		return (total, running)