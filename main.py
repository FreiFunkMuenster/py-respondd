#!/usr/bin/env python3

import sys, json

from respondd.Neighbours import Neighbours
from respondd.Nodeinfo import Nodeinfo
from respondd.Statistics import Statistics
from respondd.Cache import Cache
from respondd.Net import Net

def getConfigFromFile(argv):
	confFile = './config.json'
	if len(argv) > 0:
		confFile = argv[0]
	try:
		with open(confFile) as data_file:
			try:		
				data = json.load(data_file)
			except ValueError:
				print("Could not load config file. File may contains invalid data (ValueError).", file=sys.stderr)
				exit(1)
	except FileNotFoundError:
		print("Config file was not found (FileNotFoundError).", file=sys.stderr)
		exit(1)
	return data

def init(jsonData):
	domains = {}
	for domain in jsonData['domains']:
		domains[domain['site_code']] = {
			'neighbours' : Neighbours(domain),
			'nodeinfo' : Nodeinfo(domain, jsonData['global']),
			'statistics' : Statistics(domain)
		}
	return domains

def main(argv):
	data = getConfigFromFile(argv)
	handles = init(data)

	Cache.setTimeout(data['global']['cache_time_s'])

	net = Net(data, handles)

	# for debugging purposes only:
	# for k,v in handles.items():
	# 	v['nodeinfo'].get()
	# 	v['statistics'].get()
	# 	v['neighbours'].get()
	# print(handles['ffmsd01']['nodeinfo'].get())
	# print(handles['ffmsd01']['statistics'].get())
	# print(handles['ffmsd01']['neighbours'].get())

	net.receiver()
	
if __name__ == '__main__':
	main(sys.argv[1:])