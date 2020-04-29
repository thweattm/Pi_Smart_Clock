import json
import requests
import time, datetime
import subprocess
import re

class piholeDataClass(object):
	def __init__(self):
		self._api_url = 'http://localhost/admin/api.php'
		self.piholedata = {}
		self.raspidata = {}
		self.lastUpdated = 0
		
	def updateData(self):
		print '{} Requesting Pi-Hole Data...'.format(datetime.datetime.now().strftime("%I:%M:%S %p"))
		
		# PiHole data
		r = requests.get(self._api_url)
		self.piholedata = json.loads(r.text)
		self.lastUpdated = time.time()
		
		# IP
		cmd = "hostname -I | cut -d\' \' -f1"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		text = text.replace("\n","")
		self.raspidata['ip'] = text
		
		# Host name
		cmd = "hostname | tr -d \'\\n\'"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		self.raspidata['host'] = text

		# Memory usage
		cmd = "free -m | awk 'NR==2{printf \"%d\",$3}'"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		self.raspidata['memoryUsed'] = text
		
		cmd = "free -m | awk 'NR==2{printf \"%d\", $2}'"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		self.raspidata['memoryTotal'] = text
		
		cmd = "free -m | awk 'NR==2{printf \"%.0f\",$3*100/$2}'"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		self.raspidata['memoryPercent'] = text

		# Disk usage
		cmd = "df -h | awk '$NF==\"/\"{printf \"%d\", $3}'"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		self.raspidata['diskUsed'] = text
		
		cmd = "df -h | awk '$NF==\"/\"{printf \"%d\", $2}'"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		self.raspidata['diskTotal'] = text
		
		cmd = "df -h | awk '$NF==\"/\"{printf \"%.0f\", $5}'"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		self.raspidata['diskPercent'] = text
		
		# Uptime
		cmd = "uptime -p"
		text = subprocess.check_output(cmd, shell=True).decode("utf-8")
		#uptime = os.popen('uptime -p').readline()
		text = text.replace("\n","")
		chunks = re.split(r"[ ,]+", text)
		d = h = m = None
		for i in range (len(chunks)):
			if chunks[i] == 'days' or chunks[i] == 'day':
				d = chunks[i-1]
			elif chunks[i] == 'hours' or chunks[i] == 'hour':
				h = chunks[i-1]
			elif chunks[i] == 'minutes' or chunks[i] == 'minute':
				m = chunks[i-1]
		if not d: d = 0
		if not h: h = 0
		if not m: m = 0
		self.raspidata['pi_uptime'] = "{}d {}h {}m".format(d,h,m)
		
		print '{} OK'.format(datetime.datetime.now().strftime("%I:%M:%S %p"))
