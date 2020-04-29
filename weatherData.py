import requests
import time, datetime

class weatherDataClass(object):
	def __init__(self):
		self.data = {}
		self.lastUpdated = 0
		self._latitude = '##.###'
		self._longitude = '-##.###'
		self._apiKey = '#######################'
		self._apiURL = 'https://api.darksky.net/forecast/' + self._apiKey + '/' + self._latitude + ',' + self._longitude + '?exclude=minutely'

	# Update weather data
	def updateData(self):
		print '{} Requesting Weather Data...'.format(datetime.datetime.now().strftime("%I:%M:%S %p"))
		r = requests.get(self._apiURL)
		print '{} Status: {}'.format(datetime.datetime.now().strftime("%I:%M:%S %p"),r.status_code)
		
		r_parsed=r.json()
		r.close()

		# Pull needed contents out of parsed
		data = {'current':{},'hourly':{'data':[]},'daily':{'data':[]}}
		
		UTC_OFFSET = r_parsed['offset'] * 60 * 60

		# current metrics
		data['current']['time'] = r_parsed['currently']['time'] + UTC_OFFSET
		data['current']['summary'] = r_parsed['currently']['summary']
		data['current']['icon'] = r_parsed['currently']['icon']
		data['current']['temperature'] = r_parsed['currently']['temperature']
		data['current']['apparentTemperature'] = r_parsed['currently']['apparentTemperature']
		data['current']['windSpeed'] = r_parsed['currently']['windSpeed']
		
		# today's Stats from the daily[0] data
		data['current']['temperatureHigh'] = r_parsed['daily']['data'][0]['temperatureHigh']
		data['current']['temperatureLow'] = r_parsed['daily']['data'][0]['temperatureMin']
		data['current']['dailySummary'] = r_parsed['daily']['data'][0]['summary']
		data['current']['precipProbability'] = r_parsed['daily']['data'][0]['precipProbability'] * 100
		data['current']['precipType'] = r_parsed['daily']['data'][0]['precipType']
		data['current']['precipTime'] = r_parsed['daily']['data'][0]['precipIntensityMaxTime'] + UTC_OFFSET
		data['current']['sunriseTime'] = r_parsed['daily']['data'][0]['sunriseTime'] + UTC_OFFSET
		data['current']['sunsetTime'] = r_parsed['daily']['data'][0]['sunsetTime'] + UTC_OFFSET


		# hourly: summary, 12 hour outlook
		data['hourly']['hourlySummary'] = r_parsed['hourly']['summary']
		for d in range(1,13): # 1 - 12 in order to skip the current hour which is [0]
			data['hourly']['data'].append({'time': r_parsed['hourly']['data'][d]['time'] + UTC_OFFSET,
										   'icon': r_parsed['hourly']['data'][d]['icon'],
										   'summary': r_parsed['hourly']['data'][d]['summary'],
										   'temperature': r_parsed['hourly']['data'][d]['temperature']})

		# daily: summary, weatherData[1-6] == 6 day outlook
		data['daily']['weeklySummary'] = r_parsed['daily']['summary']
		for d in range(1,7):
			data['daily']['data'].append({'time': r_parsed['daily']['data'][d]['time'] + UTC_OFFSET,
										  'icon': r_parsed['daily']['data'][d]['icon'],
										  'temperatureHigh': r_parsed['daily']['data'][d]['temperatureHigh'],
										  'temperatureLow': r_parsed['daily']['data'][d]['temperatureMin'],
										  'summary': r_parsed['daily']['data'][d]['summary']})
		
		self.data = data
		self.lastUpdated = time.time()
