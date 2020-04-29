import time
import psutil

class utilityDataClass(object):
	def __init__(self):
		self.data = {}
		self.lastUpdated = 0

	def updateData(self):
		# CPU Loads (1min, 5min, 15min)
		self.data['load'] = psutil.getloadavg()
		self.data['load_percent'] = [x / psutil.cpu_count() * 100 for x in self.data['load']]
		
		# CPU % Usage
		self.data['cpu'] = psutil.cpu_percent()

		# CPU Temp
		temps = psutil.sensors_temperatures()
		if not temps:
			self.data['rpiTemp'] = 0
		else:
			self.data['rpiTemp'] = temps['cpu-thermal'][0].current
		
		self.lastUpdated = time.time()
