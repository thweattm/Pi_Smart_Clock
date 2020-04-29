##########################################################
#https://developers.google.com/calendar/quickstart/python
##########################################################
import time, datetime
#from datetime import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
######

class calendarDataClass(object):
	def __init__(self):
		self.data = []
		self.lastUpdated = 0

	def updateData(self):
		print '{} Requesting Calendar Data...'.format(datetime.datetime.now().strftime("%I:%M:%S %p"))
		creds = None
		# The file token.pickle stores the user's access and refresh tokens, and is
		# created automatically when the authorization flow completes for the first
		# time.
		if os.path.exists('token.pickle'):
			with open('token.pickle', 'rb') as token:
				creds = pickle.load(token)
		# If there are no (valid) credentials available, let the user log in.
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					'credentials.json', SCOPES)
				creds = flow.run_local_server(port=0)
			# Save the credentials for the next run
			with open('token.pickle', 'wb') as token:
				pickle.dump(creds, token)
			
		service = build('calendar', 'v3', credentials=creds)
		
		now = datetime.datetime.now().isoformat() + 'Z'
		data = []

		page_token = None
		while True:
			# Get the list of calendars
			calendar_list = service.calendarList().list(pageToken=page_token).execute()

			# Loop through each calendar
			for calendar_list_entry in calendar_list['items']:
				calendarName = calendar_list_entry['summary']
				color = calendar_list_entry['backgroundColor']

				# Get next 10 events from each calendar
				# This ends up with way more events than I can list, but ensures
				# enough items in case of empty calendars.
				events_result = service.events().list(calendarId=calendar_list_entry['id'], timeMin=now,
														maxResults=10, singleEvents=True,
														orderBy='startTime').execute()
				events = events_result.get('items', [])

				if not events:
					pass #print('No upcoming events found.')

				for event in events:
					if event['start'].get('dateTime'):
						allDay = False
					else:
						allDay = True
					
					data.append({'color':color,
								'summary':event['summary'],
								'allDay':allDay,
								'dateTime': event['start'].get('dateTime', event['start'].get('date')),
								'endTime': event['end'].get('dateTime', event['end'].get('date'))})

			page_token = calendar_list.get('nextPageToken')
			if not page_token:
				break

		data.sort(key=lambda entry: entry['dateTime'])
		self.data = data[0:15] # Keep only some of them to save space since the screen size is limited anyway

		self.lastUpdated = time.time()
		print '{} OK'.format(datetime.datetime.now().strftime("%I:%M:%S %p"))
