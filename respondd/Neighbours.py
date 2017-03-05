import string, subprocess, netifaces
from .Cache import Cache
from .BasicNode import BasicNode
class Neighbours(BasicNode):
	TT = dict.fromkeys(map(ord, '*[]()'), None)
	def __init__(self, domain):
		self.domain = domain
		self.ifMacs = {}

	def get(self):


		return {
			'batadv': self.getNeights(),
			'node_id' : self.getMacAddr().replace(':',''),
		}


	def getNeights(self):
		return Cache.getLocal('bat_stats', self.domain['site_code'], self.updateNeights)

	def updateNeights(self, *args):
		res = {}
		out, err = self.execBatProcess()
		
		out = str(out, 'utf-8')

		for line in out.splitlines()[2:-1]:
			line = [x for x in line.translate(Neighbours.TT).split()]

			# remove colon that occours in older batman versions only
			ifName = line[4].replace(':', '')

			if len(line) == 0:
				# skip empty lines
				continue
			if line[0] != line[3]:
				# skip indirect links
				continue

			# fetch mac for interface and init dict
			if ifName not in self.ifMacs:
				ifMac = netifaces.ifaddresses(ifName)[netifaces.AF_LINK][0]['addr']
				self.ifMacs[ifName] = ifMac
				res[ifMac] = {'neighbours': {}}
			else:
				ifMac = self.ifMacs[ifName]
				if ifMac not in res:
					res[ifMac] = {'neighbours': {}}

			# add neighbour to interface
			res[ifMac]['neighbours'][line[0]] = {
				'tq': int(line[2]),
				'lastseen': float(line[1][:-1])
			}
		return res

	def execBatProcess(self):
		return Cache.getLocal('bat_process_o', self.domain['site_code'], self.updateBatProcess)

	def updateBatProcess(self, *args):
		p = subprocess.Popen(['batctl', '-m', self.domain['bat_iface'], 'o'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		return p.communicate()