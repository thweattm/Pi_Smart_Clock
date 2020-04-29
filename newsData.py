import time, datetime
import requests
from random import shuffle

class newsDataClass(object):
	def __init__(self):
		self.data = {}
		self.lastShuffle = time.time()
		self.lastUpdated = 0
		self._apiKey = '#########################'
		self._apiURL = 'http://newsapi.org/v2/top-headlines?country=us&apiKey=' + self._apiKey

	def updateNews(self):
		# 500 requests per day = free
		print '{} Requesting News Data...'.format(datetime.datetime.now().strftime("%I:%M:%S %p"))
		r = requests.get(self._apiURL)
		print '{} Status: {}'.format(datetime.datetime.now().strftime("%I:%M:%S %p"),r.status_code)
		self.data = r.json()
		r.close()
		self.lastUpdated = time.time()
		self.lastShuffle = time.time()

	def shuffleArticles(self):
		# Shuffle articles array
		shuffle(self.data['articles'])
		self.lastShuffle = time.time()
