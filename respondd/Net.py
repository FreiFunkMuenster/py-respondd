import struct, socket, fcntl, json, zlib
from respondd.Cache import Cache

class Net(object):
	SIOCGIFADDR = 0x8915
	def __init__(self, config, handles):
		self.globalData = config['global']
		self.group = self.globalData['mcast_group']
		self.port = self.globalData['port']
		self.handles = handles
		self.interface = None
		self.ifToSite = self.genIfToSite(config['domains'])
		self.sock = self.bindSock()

	def bindSock(self):
		addrinfo = socket.getaddrinfo(self.group, None)[0]

		s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

		s.bind(('', self.port))

		group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])

		if self.interface == None:
			mreq = group_bin + struct.pack('@I', 0)
		else:
			ip_addr = self.get_ip_address(self.interface)
			ip_addr_n = socket.inet_aton(ip_addr)
			mreq = group_bin + struct.pack("=4s", ip_addr_n)

		s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)
		return s

	def receiver(self):


		while True:
			Cache.updateTime()
			data, sender = self.sock.recvfrom(1500)
			while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
			self.handleRequest(sender,data)

	def genIfToSite(self, domains):
		res = {}
		for dom in domains:
			res[dom['bat_iface']] = dom['site_code']
		return res

	def handleRequest(self, sender, data):
		if not data.startswith(b'GET '):
			# unknown request
			return

		requestTypes = str(data[4:], 'utf-8').split(' ')

		senderAddr, interface = sender[0].split('%')

		site = self.ifToSite[interface]

		if site not in self.handles:
			# unconfigured domain
			return
		for requestType in requestTypes:
		#	print(requestType, senderAddr, interface, site)
			message = {}
			message[requestType] = self.handles[site][requestType].get()
			self.sender(message,sender)


	def sender(self, message, sender):
		message = bytes('{}'.format(json.dumps(message)), 'utf-8')
		message = zlib.compress(message)[2:-4]
		self.sock.sendto(message + b'\0', sender)

	def get_ip_address(self, ifname):
		return socket.inet_ntoa(fcntl.ioctl(self.sock.fileno(), Net.SIOCGIFADDR, struct.pack('256s', ifname[:15]))[20:24])
