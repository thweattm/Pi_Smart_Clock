#!/usr/bin/python

from calendarData import calendarDataClass
from newsData import newsDataClass
from utilityData import utilityDataClass
from weatherData import weatherDataClass
from screen import screenClass
from piholeData import piholeDataClass

import datetime
from dateutil.parser import parse as dtparse
from random import randint
import time

#import subprocess
import sys, traceback
import pygame
import evdev
import select
#import math


################################################
# Load main pygame surfaces
screenWidth = 480
screenHeight = 320
pygame.init()
pygame.font.init()
clock = pygame.time.Clock()
FPS = 60
# adjusted PITFT settings to increase performance and refresh rate on display
# learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/faq?view=all
# under FAQ: "I want better performance and faster updates!"
# edit: /boot/config.txt
# set to maximum: 'dtoverlay=pitft28r,rotate=270,speed=62500000,fps=60
# This in turn helped smooth out the screen slide animation a bit
################################################

# Fonts & Colors
tinyFont = pygame.font.SysFont("Arial",12)
newsFont = pygame.font.SysFont("Arial",16)
smallFont = pygame.font.SysFont("Arial",18)
dateFont = pygame.font.SysFont("Arial",25)
timeFont = pygame.font.SysFont("Arial",45)
tempFont = pygame.font.SysFont("Arial",35)

RGB_WHITE = (255,255,255)
RGB_GRAY = (128,128,128)
RGB_BLACK = (0,0,0)
RGB_BLUE = (77,166,255)
RGB_YELLOW = (255,255,0)
RGB_GREEN = (0,204,0)
RGB_RED = (255,0,0)


################################################
# Variables for the touch screen input functions
tftOrig = (3750, 180)
tftEnd = (150, 3750)
tftDelta = (tftEnd [0] - tftOrig [0], tftEnd [1] - tftOrig [1])
tftAbsDelta = (abs(tftEnd [0] - tftOrig [0]), abs(tftEnd [1] - tftOrig [1]))
touch = evdev.InputDevice('/dev/input/touchscreen')
touch.grab()
#print(touch) # prints some info about the touch screen

# Helper to get pixels from touch screen map
def getPixelsFromCoordinates(coords):
    # TODO check divide by 0!
    if tftDelta [0] < 0:
        x = float(tftAbsDelta [0] - coords [0] + tftEnd [0]) / float(tftAbsDelta [0]) * float(screenWidth)
    else:    
        x = float(coords [0] - tftOrig [0]) / float(tftAbsDelta [0]) * float(screenWidth)
    if tftDelta [1] < 0:
        y = float(tftAbsDelta [1] - coords [1] + tftEnd [1]) / float(tftAbsDelta [1]) * float(screenHeight)
    else:        
        y = float(coords [1] - tftOrig [1]) / float(tftAbsDelta [1]) * float(screenHeight)
    return (int(x), int(y))
################################################



# return the rgb code for the associated hex value
def convertCalendarColor(h):
	hColors = {'#cca6ac':(204,166,172), 	# holiday: pinkish
				'#7bd148':(123,209,72),		# default: green
				'#cd74e6':(205,116,230),	# secondary: purple
				'#4986e7':(73,134,231)}		# work: blue
	
	if h in hColors:
		return hColors[h]
	else:
		return RGB_GRAY # gray
		
			

#################################################
# Process incoming touch points - map to buttons
#################################################
def processTouch(p, PITFT):
	# return item that was touched, if any
	#p[0] = x, p[1] = y
	global CURRENT_SCREEN, SCREEN_ROTATE, REDRAW, FULL_REDRAW, rotateTime, lastPowerOffCheck, SLIDE_DIRECTION
	global AUTO_SLEEP, SHOW_MENU, SCREEN_SAVER, CONFIRM_REBOOT, CONFIRM_SHUTDOWN, REBOOTING, SHUTTING_DOWN
	
	#Disable Sleep mode?
	if SCREEN_SAVER or not PITFT.screenOn:
		print "{} Disabling screen saver and/or turning on LCD...".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
		SCREEN_SAVER = False
		FULL_REDRAW = True
		# Turn back on LCD if needed
		if not PITFT.screenOn:
			print "{} Turning LCD back on from touch wake...".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
			PITFT.backlightOn()
			lastPowerOffCheck = 0
	
	elif REBOOTING or SHUTTING_DOWN:
		print "{} Ignore due to reboot or shut down...".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
		#REBOOTING = SHUTTING_DOWN = False
		
	elif CONFIRM_REBOOT or CONFIRM_SHUTDOWN:
		# check y coordinates, then x coordinates
		if p[1] <= 235 and p[1] >= 185:
			
			# Yes
			if p[0] < 240 and p[0] >= 115:
				# Reboot
				if CONFIRM_REBOOT:
					print "{} Reboot confirmed, rebooting in 5 seconds.".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					mainSurface.blit(drawMsgBoxSurface("reboots"),(115,85))
					PITFT.refresh()
					time.sleep(5)
					mainSurface.fill(RGB_BLACK)
					PITFT.refresh()
					PITFT.reboot()
					REBOOTING = True
					CONFIRM_REBOOT = CONFIRM_SHUTDOWN = False
				
				# Shutdown
				elif CONFIRM_SHUTDOWN:
					print "{} Shutdown confirmed, shutting down in 5 seconds".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					mainSurface.blit(drawMsgBoxSurface("shuts down"),(115,85))
					PITFT.refresh()
					time.sleep(5)
					mainSurface.fill(RGB_BLACK)
					PITFT.refresh()
					PITFT.shutdown()
					SHUTTING_DOWN = True
					CONFIRM_REBOOT = CONFIRM_SHUTDOWN = False
			
			# No	
			elif p[0] <= 365 and p[0] > 240:
				print "{} Cancelling reboot request...".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
				CONFIRM_REBOOT = CONFIRM_SHUTDOWN = False
				mainSurface.blit(drawMenuSurface(),(0, 0))
			
	else:
		if SHOW_MENU:
			if p[0] < 240:
				if p[1] < 55:
					print "{} Menu - Back Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					slideMenuClose()
					SHOW_MENU = False
					
				elif p[1] < 105:
					print "{} Menu - Reboot Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					CONFIRM_REBOOT = True
					
				elif p[1] < 155:
					print "{} Menu - Shutdown Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					CONFIRM_SHUTDOWN = True
					
				elif p[1] < 205:
					print "{} Menu - Screensaver Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					SCREEN_SAVER = True
					SHOW_MENU = False
					
				elif p[1] < 255:
					print "{} Menu - Sleep Mode Button Pressed, turning of LCD".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					SHOW_MENU = False
					PITFT.backlightOff()
					
				else:
					print "{} Menu - Auto Sleep Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					AUTO_SLEEP = not AUTO_SLEEP
					lastPowerOffCheck = 0

			else:
				print "{} Input touch not defined".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
		else:
			# Top Row
			if p[1] <= 45:
				# Main Menu
				if p[0] < 50:
					print "{} Main Menu Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					slideMenuOpen()
					SHOW_MENU = True
					
				# Hourly Weather Button
				elif p[0] >= 245 and p[0] < 293:
					print "{} Hourly Weather Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					if CURRENT_SCREEN == 1:
						SCREEN_ROTATE = not SCREEN_ROTATE
						rotateTime = time.time()
					else:	
						if 1 < CURRENT_SCREEN:
							SLIDE_DIRECTION = "right"
						else:
							SLIDE_DIRECTION = "left"
						CURRENT_SCREEN = 1
						SCREEN_ROTATE = False
						REDRAW = True
					mainSurface.blit(drawIconUnderline(),(241,41))
				
				# Daily Weather Button
				elif p[0] >= 293 and p[0] < 339:
					print "{} Daily Weather Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					if CURRENT_SCREEN == 2:
						SCREEN_ROTATE = not SCREEN_ROTATE
						rotateTime = time.time()
					else:
						if 2 < CURRENT_SCREEN:
							SLIDE_DIRECTION = "right"
						else:
							SLIDE_DIRECTION = "left"
						CURRENT_SCREEN = 2
						SCREEN_ROTATE = False
						REDRAW = True
					mainSurface.blit(drawIconUnderline(),(241,41))
				
				# News Button
				elif p[0] >= 339 and p[0] < 392:
					print "{} News Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					if CURRENT_SCREEN == 3:
						SCREEN_ROTATE = not SCREEN_ROTATE
						rotateTime = time.time()
					else:
						if 3 < CURRENT_SCREEN:
							SLIDE_DIRECTION = "right"
						else:
							SLIDE_DIRECTION = "left"
						CURRENT_SCREEN = 3
						SCREEN_ROTATE = False
						REDRAW = True
					mainSurface.blit(drawIconUnderline(),(241,41))
				
				# Calendar Button
				elif p[0] >= 392 and p[0] < 437:
					print "{} Calendar Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					if CURRENT_SCREEN == 4:
						SCREEN_ROTATE = not SCREEN_ROTATE
						rotateTime = time.time()
					else:
						if 4 < CURRENT_SCREEN:
							SLIDE_DIRECTION = "right"
						else:
							SLIDE_DIRECTION = "left"
						CURRENT_SCREEN = 4
						SCREEN_ROTATE = False
						REDRAW = True
					mainSurface.blit(drawIconUnderline(),(241,41))
					
				# PiHole button
				elif p[0] > 437:
					print "{} PiHole Button Pressed".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
					if CURRENT_SCREEN == 5:
						SCREEN_ROTATE = not SCREEN_ROTATE
						rotateTime = time.time()
					else:
						if 5 < CURRENT_SCREEN:
							SLIDE_DIRECTION = "right"
						else:
							SLIDE_DIRECTION = "left"
						CURRENT_SCREEN = 5
						SCREEN_ROTATE = False
						REDRAW = True
					mainSurface.blit(drawIconUnderline(),(241,41))

				else:
					print "{} Input touch not defined".format(datetime.datetime.now().strftime("%I:%M:%S %p"))
			
			else:
				print "{} Input touch not defined".format(datetime.datetime.now().strftime("%I:%M:%S %p"))



########################################################################################################
# Function to take a string of text and parse line breaks plus ability to justify text
# https://stackoverflow.com/questions/32590131/pygame-blitting-text-with-an-escape-character-or-newline
########################################################################################################
class TextRectException:
    def __init__(self, message=None):
            self.message = message

    def __str__(self):
        return self.message

def multiLineSurface(string, font, rect, fontColour, BGColour, justification=0):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Parameters
    ----------
    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rect style giving the size of the surface requested.
    fontColour - a three-byte tuple of the rgb value of the
             text color. ex (0, 0, 0) = BLACK
    BGColour - a three-byte tuple of the rgb value of the surface or None for transparent.
    justification - 0 (default) left-justified
                1 horizontally centered
                2 right-justified

    Returns
    -------
    Success - a surface object with the text rendered onto it and count of lines
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """

    finalLines = []
    requestedLines = string.splitlines()
    # Create a series of lines that will fit on the provided
    # rectangle.
    for requestedLine in requestedLines:
        if font.size(requestedLine)[0] > rect.width:
            words = requestedLine.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
					raise TextRectException("The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulatedLine = ""
            for word in words:
                testLine = accumulatedLine + word + " "
                # Build the line while the words fit.
                if font.size(testLine)[0] < rect.width:
                    accumulatedLine = testLine
                else:
                    finalLines.append(accumulatedLine)
                    accumulatedLine = word + " "
            finalLines.append(accumulatedLine)
        else:
            finalLines.append(requestedLine)

    # Let's try to write the text out on the surface.
    surface = pygame.Surface(rect.size,pygame.SRCALPHA)
    if BGColour:
		surface.fill(BGColour)
    accumulatedHeight = 0
    for line in finalLines:
        if accumulatedHeight + font.size(line)[1] >= rect.height:
            raise TextRectException("Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempSurface = font.render(line, 1, fontColour)
        if justification == 0:
            surface.blit(tempSurface, (0, accumulatedHeight))
            accumulatedHeight += font.size(line)[1] - 2
        elif justification == 1:
            surface.blit(tempSurface, ((rect.width - tempSurface.get_width()) / 2, accumulatedHeight))
            accumulatedHeight += font.size(line)[1] - 2
        elif justification == 2:
            surface.blit(tempSurface, (rect.width - tempSurface.get_width(), accumulatedHeight))
            accumulatedHeight += font.size(line)[1] - 2
        else:
            raise TextRectException("Invalid justification argument: " + str(justification))
		
    return surface, accumulatedHeight
###############################################################################################


'''
##############################################################
# Drawing Functions
##############################################################
'''

'''
#####################################
#      LEFT SIDE PANEL ITEMS        #
#####################################
'''
# Draw date & time
def drawClock():
	surfaceHeight = 82
	surfaceWidth = 239		# remove 1px from right side to not write over middle divider line
	
	# Create surface
	clockSurface = pygame.Surface((surfaceWidth, surfaceHeight),pygame.SRCALPHA)
	clockSurface.blit(backgroundSurface, (0,0), (0,0,surfaceWidth,surfaceHeight))
	
	# Main menu icon
	clockSurface.blit(pygame.image.load('./graphics/main_menu_graphics/menu.png'),(0, 3))
	
	# Date
	text = dateFont.render(now.strftime("%a %b %d"), False, RGB_WHITE)
	textWidth = text.get_width()
	textHeight = text.get_height()
	clockSurface.blit(text, ((surfaceWidth + 1) // 2 - textWidth // 2, 2))
	
	# Time
	text = timeFont.render(now.strftime("%I:%M %p"), False, RGB_WHITE)
	textWidth = text.get_width()
	textHeight = text.get_height()
	clockSurface.blit(text, ((surfaceWidth + 1) // 2 - textWidth // 2, 27))
	pygame.draw.line(clockSurface, RGB_GRAY, (5,81), (235,81))
	
	# Auto Sleep Check active icon
	if powerOffCheck:
		clockSurface.blit(pygame.image.load('./graphics/misc_icons/autosleep.png'),(208, 0))

	return clockSurface


# Draw current weather surface
def drawCurrentWeather():
	surfaceTop = 83			# y value for top of available space
	surfaceBottom = 284		# y value for bottom of available space
	surfaceHeight = surfaceBottom - surfaceTop
	surfaceWidth = 239		# remove 1px from right side to not write over middle divider line
	
	# Create surface
	weatherSurface = pygame.Surface((surfaceWidth, surfaceHeight))
	weatherSurface.blit(backgroundSurface, (0,0), (0,surfaceTop,surfaceWidth,surfaceHeight))
	
	# Get surface for summary text as the rest of the screen is formatted around this height
	box = pygame.Surface((240,43),pygame.SRCALPHA)
	rect = box.get_rect()
	s = weather.data['current']['dailySummary']
	#s = 'two line test right here\ntwo line test right here'
	#s = 'three line test right here\nthree line test right here\nthree line test right here'
	tinyFont.set_bold(True)
	fontHeight = tinyFont.render(s, False, RGB_WHITE).get_height()
	summaryTextBox,summaryHeight = multiLineSurface(s, tinyFont, rect, RGB_WHITE, None, 1)
	tinyFont.set_bold(False)
	
	# Set padding and spacing depending on how tall the summary text is
	if summaryHeight < fontHeight:
		padding = 4
	elif summaryHeight < fontHeight * 2:
		padding = 2
	else:
		padding = 1
	
	###############################
	# Top Half - Main larger stats
	###############################
	# x, y section starting positions
	y = padding
	x = 105
	
	# Current weather Icon
	s = './graphics/weather_large/' + weather.data['current']['icon'] + '.png'
	weatherSurface.blit(pygame.image.load(s),(0, y+2))
	
	# Current weather Temp
	s = "{0:.0f}".format(weather.data['current']['temperature']) + u'\u00b0' + "F"
	text = tempFont.render(s, False, RGB_WHITE)
	weatherSurface.blit(text,(x, y + padding))
	y += (text.get_height() + padding)
	
	# High / Low
	smallFont.set_bold(True)
	weatherSurface.blit(pygame.image.load('./graphics/misc_icons/tempHigh.png'),(x-8, y))
	weatherSurface.blit(pygame.image.load('./graphics/misc_icons/tempLow.png'),(x+55, y))
	s = "{0:.0f}".format(weather.data['current']['temperatureHigh']) + u'\u00b0'
	weatherSurface.blit(smallFont.render(s, False, RGB_WHITE),(x+17, y+3))
	s = "{0:.0f}".format(weather.data['current']['temperatureLow']) + u'\u00b0'
	weatherSurface.blit(smallFont.render(s, False, RGB_WHITE),(x+80, y+3))
	
	# Current condition text
	y += (25 + padding)
	text = smallFont.render(weather.data['current']['summary'], False, RGB_WHITE)
	weatherSurface.blit(text,(x, y))
	smallFont.set_bold(False)
	
	y += (text.get_height() + padding + 5)
	pygame.draw.line(weatherSurface, RGB_GRAY, (5,y), (235,y))
	
	#######################################
	# Bottom Half - Smaller extra stats
	#######################################
	x1 = 14 		# left column of items
	x2 = 116		# right column of items
	y += padding	# starting y pos
	steps = 30		# y space between rows
	
	# Set row spacing depending on summary text height
	'''if summaryHeight < fontHeight: # 1 Row of text
		rowSpace = 10 	# gap between summary and other stats
		y += padding 	# double the top padding
	'''
	if summaryHeight < fontHeight * 2: # One or two rows of text
		rowSpace = 10	# gap between summary and other stats
		y += padding 	# double the top padding
	
	else: # 3 or more rows of text
		rowSpace = 6	# gap between summary and other stats
		y -= (padding//2) # remove some top padding
	
	# Daily summary
	weatherSurface.blit(summaryTextBox, (0,y))
	y += (summaryHeight + rowSpace)
	
	# Row 1 = Real Feel / Sun Rise
	weatherSurface.blit(pygame.image.load('./graphics/misc_icons/realfeel.png'),(x1, y))
	s = "{:.0f}".format(weather.data['current']['apparentTemperature']) + u'\u00b0'
	weatherSurface.blit(smallFont.render(s, False, RGB_WHITE),(x1+30, y+7))
	
	weatherSurface.blit(pygame.image.load('./graphics/misc_icons/sunrise.png'),(x2, y))
	theTime = datetime.datetime.utcfromtimestamp(weather.data['current']['sunriseTime']).strftime('%-I:%M %p')
	s = "{}".format(theTime)
	weatherSurface.blit(smallFont.render(s, False, RGB_WHITE),(x2+35, y+7))
	
	# Row 2 = Wind Speed / Sun Set
	y += steps
	weatherSurface.blit(pygame.image.load('./graphics/misc_icons/windsock.png'),(x1, y))
	weatherSurface.blit(smallFont.render("{:.0f} mph".format(weather.data['current']['windSpeed']), False, RGB_WHITE),(x1+30, y+7))
	
	weatherSurface.blit(pygame.image.load('./graphics/misc_icons/sunset.png'),(x2, y))
	theTime = datetime.datetime.utcfromtimestamp(weather.data['current']['sunsetTime']).strftime('%-I:%M %p')
	s = "{}".format(theTime)
	weatherSurface.blit(smallFont.render(s, False, RGB_WHITE),(x2+35, y+7))
	
	return weatherSurface
	

# Draw bottom utility stats
def drawUtilityStats():
	surfaceHeight = 35
	surfaceWidth = 239		# remove 1px from right side to not write over middle divider line
	
	# Create surface
	utilitySurface = pygame.Surface((surfaceWidth, surfaceHeight),pygame.SRCALPHA)
	utilitySurface.blit(backgroundSurface, (0,0), (0,285,surfaceWidth,surfaceHeight))
	pygame.draw.line(utilitySurface, RGB_GRAY, (5,0), (235,0))
	
	# Weather last updated
	s = "Weather Last Updated: {}".format(datetime.datetime.utcfromtimestamp(weather.data['current']['time']).strftime('%-I:%M %p'))
	text = tinyFont.render(s, False, RGB_BLUE)
	textWidth = text.get_width()
	utilitySurface.blit(text, ((surfaceWidth + 1) // 2 - textWidth // 2, 5))

	# CPU stats / Temperature stats
	if utilities.data['cpu'] >= 75:
		font_color = RGB_RED
	else:
		font_color = RGB_GREEN
	cpuText = "CPU: {:.0f}%  ".format(utilities.data['cpu'])
	cpuText = tinyFont.render(cpuText, False, font_color)
	
	if utilities.data['rpiTemp'] >= 80:
		font_color = RGB_RED
	else:
		font_color = RGB_GREEN
	tempText = "Temp: {:.1f}".format(utilities.data['rpiTemp'])
	tempText += u'\u00b0' + "C"
	tempText = tinyFont.render(tempText, False, font_color)
	
	combinedText = pygame.Surface((cpuText.get_width()+tempText.get_width(), max(cpuText.get_height(), tempText.get_height())),pygame.SRCALPHA)
	combinedText.blit(cpuText,(0,0))
	combinedText.blit(tempText,(cpuText.get_width()+1,0))
	combinedWidth = combinedText.get_width()
	
	utilitySurface.blit(combinedText, ((surfaceWidth + 1) // 2 - combinedWidth // 2, 20))
	
	#s = "CPU: {:.0f}%  Temp: {:.1f}".format(utilities.data['cpu'], utilities.data['rpiTemp'])
	#s += u'\u00b0' + "C"
	
	#text = tinyFont.render(s, False, RGB_WHITE)
	#textWidth = text.get_width()
	#utilitySurface.blit(text, ((surfaceWidth + 1) // 2 - textWidth // 2, 20))

	return utilitySurface



'''
#####################################
#      RIGHT SIDE PANEL ITEMS       #
#####################################
'''
# Draw the top right menu of icons (not the line underneath active icon however)
def drawTopRightIcons():
	# This panel is pasted 1px right of center,
	# thus x = 0 here is really center + 1px on main
	
	surfaceHeight = 46
	surfaceWidth = 239		# remove 1px from left to not write over middle divider line
	
	iconSurface = pygame.Surface((surfaceWidth, surfaceHeight))
	iconSurface.blit(backgroundSurface, (0,0), (246,0,surfaceWidth,surfaceHeight))
	
	x = 6 # Starting x
	# Weather Hourly
	iconSurface.blit(pygame.image.load('./graphics/screen_selector_icons/weather_hourly.png'),(x, 5))
	x+= 48
	# Weather Daily
	iconSurface.blit(pygame.image.load('./graphics/screen_selector_icons/weather_daily.png'),(x, 5))
	x+= 46
	# News
	iconSurface.blit(pygame.image.load('./graphics/screen_selector_icons/news.png'),(x, 0))
	x+= 53
	# Calendar
	iconSurface.blit(pygame.image.load('./graphics/screen_selector_icons/calendar.png'),(x, 5))
	x+= 47
	# PiHole
	iconSurface.blit(pygame.image.load('./graphics/screen_selector_icons/rpi.png'),(x, 6))
	# Divider Line below icons
	pygame.draw.line(iconSurface, RGB_GRAY, (4,45), (surfaceWidth-5,45))

	return iconSurface



# Draw Green or Red line under active screen
def drawIconUnderline():
	# This panel is pasted 1px right of center,
	# thus x = 0 here is really center + 1px on main
	lineLength = 30
	y = 0
	surfaceHeight = 1
	surfaceWidth = 239		# remove 1px from left to not write over middle divider line
	
	lineSurface = pygame.Surface((surfaceWidth, surfaceHeight))
	lineSurface.blit(backgroundSurface, (0,0), (246,41,surfaceWidth,surfaceHeight))
	
	# Green = rotate ON, red = rotate OFF
	if SCREEN_ROTATE:
		theColor = RGB_GREEN
	else:
		theColor = RGB_RED
		
	if CURRENT_SCREEN == 1:
		x = 9
	elif CURRENT_SCREEN == 2:
		x = 56
	elif CURRENT_SCREEN == 3:
		x = 106
	elif CURRENT_SCREEN == 4:
		x = 155
	elif CURRENT_SCREEN == 5:
		x = 198

	pygame.draw.line(lineSurface, theColor, (x,y), (x + lineLength ,y))
	return lineSurface
	
	
	
# Create the base surface for the right side panels
def rightSideBaseSurface():
	surfaceHeight = 274 	# remove 1px from height to not overwrite menu separator line
	surfaceWidth = 230		# remove 10px from width for padding on sides
	newSurface = pygame.Surface((surfaceWidth, surfaceHeight))
	# blit a cropped portion of background surface to this surface
	# box.blit(source_surface, (x,y coordinates of box = x,y placement within new_surface), (x,y,width,height of source_surface cropping))
	newSurface.blit(backgroundSurface, (0,0), (245,46,surfaceWidth,surfaceHeight))
	return newSurface



# Draw hourly outlook surface
def drawHourlyOutlook():
	# This panel is pasted 5px right of center,
	# thus x = 0 here is really center + 5px on main
	
	surfaceHeight = 274 	# remove 1px from height to not overwrite menu separator line
	surfaceWidth = 230		# remove 10px from width for padding on sides
	middle = surfaceWidth // 2
	y = 4
	
	numRows = 4
	outlookSurface = rightSideBaseSurface()
	
	h = 0
	
	for i in range(numRows):
		lineStart = y + 1
		# Icon (left column)
		s = './graphics/weather_mini/' + weather.data['hourly']['data'][h]['icon'] + '.png'
		outlookSurface.blit(pygame.image.load(s),(70, y))
		# Icon (right column)
		s = './graphics/weather_mini/' + weather.data['hourly']['data'][h+1]['icon'] + '.png'
		outlookSurface.blit(pygame.image.load(s),(middle+75, y))
		# Time (left column)
		s = datetime.datetime.utcfromtimestamp(weather.data['hourly']['data'][h]['time']).strftime('%-I %p')
		outlookSurface.blit(smallFont.render(s, False, RGB_BLUE),(5, y))
		# Time (right column)
		s = datetime.datetime.utcfromtimestamp(weather.data['hourly']['data'][h+1]['time']).strftime('%-I %p')
		outlookSurface.blit(smallFont.render(s, False, RGB_BLUE),(middle+10, y))
		y += 20
		# Temperature (left column)
		s = "{0:.0f}".format(weather.data['hourly']['data'][h]['temperature']) + u'\u00b0'
		outlookSurface.blit(smallFont.render(s, False, RGB_WHITE),(5, y))
		# Temperature (right column)
		s = "{0:.0f}".format(weather.data['hourly']['data'][h+1]['temperature']) + u'\u00b0'
		outlookSurface.blit(smallFont.render(s, False, RGB_WHITE),(middle+10, y))
		y += 20
		#Summary (left column)
		s = weather.data['hourly']['data'][h]['summary']
		outlookSurface.blit(newsFont.render(s, False, RGB_WHITE),(5, y))
		#Summary (right column)
		s = weather.data['hourly']['data'][h+1]['summary']
		outlookSurface.blit(newsFont.render(s, False, RGB_WHITE),(middle+10, y))
		y += 24
		# Line separator
		# Middle verticle line
		pygame.draw.line(outlookSurface, RGB_GRAY, (middle,lineStart), (middle,y-5))
		if i < numRows -1:
			# Bottom horizontal line
			pygame.draw.line(outlookSurface, RGB_GRAY, (0,y), (surfaceWidth,y))
			y += 4
		h += 2
	
	''' previous 6 hour full row version:
	numHours = 6

	# x references for each item
	x_time = 5
	x_icon = 70
	x_text = 115
	
	y = 0
	steps = 45.85 # Row height esstentially
	
	outlookSurface = rightSideBaseSurface()
	
	for i in range(numHours):
		# Time
		s = datetime.datetime.utcfromtimestamp(weather.data['hourly']['data'][i]['time']).strftime('%-I %p')
		text = smallFont.render(s, False, RGB_BLUE)
		textHeight = text.get_height()
		yPad = steps // 2 - textHeight // 2
		outlookSurface.blit(text,(x_time, y + yPad))
		
		# Icon
		s = './graphics/weather_mini/' + weather.data['hourly']['data'][i]['icon'] + '.png'
		outlookSurface.blit(pygame.image.load(s),(x_icon, y+3))
		
		# Temperature + Summary string
		s = "{0:.0f}".format(weather.data['hourly']['data'][i]['temperature']) + u'\u00b0'
		s += ' ' + weather.data['hourly']['data'][i]['summary']
		text = smallFont.render(s, False, RGB_WHITE)
		textHeight = text.get_height()

		# Take care of any text wrapping
		box = pygame.Surface((110,(steps*2)),pygame.SRCALPHA)
		textRect = box.get_rect(topleft=(0,0))
		textBox,accumulatedHeight = multiLineSurface(s, smallFont, textRect, RGB_WHITE, None, 1)
		
		# Vertically center text
		yPad = steps // 2 - accumulatedHeight // 2
		outlookSurface.blit(textBox,(x_text, y + yPad - 1)) # Minus an extra px for better centering
		
		y += steps
		
		# Line separator
		pygame.draw.line(outlookSurface, RGB_GRAY, (0,y), (surfaceWidth,y))
	'''	
	return outlookSurface
						
						
						

# Draw daily outlook surface
def drawDailyOutlook():
	# This panel is pasted 5px right of center,
	# thus x = 0 here is really center + 5px on main
	
	surfaceHeight = 274 	# remove 1px from height to not overwrite menu separator line
	surfaceWidth = 230		# remove 10px from width for padding on sides
	numDays = 6
						
	# x references for each item of each 'row' (easier to see here vs below)
	x_day = 5
	x_icon = 68
	x_highIcon = 112
	x_highText = 136
	x_lowIcon = 169
	x_lowText = 192
	
	y = 0
	steps = 45.85 # Row height esstentially
	
	outlookSurface = rightSideBaseSurface()
	
	for i in range(numDays):
		# Day of week
		s = datetime.datetime.utcfromtimestamp(weather.data['daily']['data'][i]['time']).strftime('%a')
		outlookSurface.blit(smallFont.render(s, False, RGB_BLUE),(x_day, y+2))
		s = datetime.datetime.utcfromtimestamp(weather.data['daily']['data'][i]['time']).strftime('%b %d')
		outlookSurface.blit(smallFont.render(s, False, RGB_BLUE),(x_day, y+20))
		
		# Icon
		s = './graphics/weather_mini/' + weather.data['daily']['data'][i]['icon'] + '.png'
		outlookSurface.blit(pygame.image.load(s),(x_icon, y+3))
		
		# High
		outlookSurface.blit(pygame.image.load('./graphics/misc_icons/tempHigh.png'),(x_highIcon, y+10))
		s = "{0:.0f}".format(weather.data['daily']['data'][i]['temperatureHigh']) + u'\u00b0'
		outlookSurface.blit(smallFont.render(s, False, RGB_WHITE),(x_highText, y+13))
		
		# Low
		outlookSurface.blit(pygame.image.load('./graphics/misc_icons/tempLow.png'),(x_lowIcon, y+10))
		s = "{0:.0f}".format(weather.data['daily']['data'][i]['temperatureLow']) + u'\u00b0'
		outlookSurface.blit(smallFont.render(s, False, RGB_WHITE),(x_lowText, y+13))
	
		y += steps
		
		# Line separator
		pygame.draw.line(outlookSurface, RGB_GRAY, (0,y), (surfaceWidth,y))
	
	return outlookSurface	
							
							

# Draw news surface
def drawNewsSurface():
	# This panel is pasted 5px right of center,
	# thus x = 0 here is really center + 5px on main
	
	surfaceHeight = 274 	# remove 1px from height to not overwrite menu separator line
	surfaceWidth = 230		# remove 10px from width for padding on sides
	y = 0
	
	newsSurface = rightSideBaseSurface()

	if not news.data['totalResults'] or news.data['totalResults'] <= 0:
		newsSurface.blit(smallFont.render("No articles available", False, RGB_WHITE),(3, 3))
		
	else:
		# Loop through articles while there is still space
		for article in news.data['articles']:
			headline = article['title']
			
			# Box is taller than should be needed, but just to be safe
			box = pygame.Surface((surfaceWidth-4,surfaceHeight),pygame.SRCALPHA)
			rect = box.get_rect(topleft=(0,0))
			textBox,accumulatedHeight = multiLineSurface(headline, newsFont, rect, RGB_WHITE, None, 1)
			
			# If the headline can fit into the remaining space:
			if accumulatedHeight + 3 <= (surfaceHeight-y):
				# Draw line above headline (only if not the first article)
				if y > 0:
					pygame.draw.line(newsSurface, RGB_GRAY, (0,y), (surfaceWidth,y))
				# Draw text box
				newsSurface.blit(textBox,(2, y+3))
				
				# advance y axis with some padding
				y += accumulatedHeight + 8
									
									
	return newsSurface					
									


# Draw calendar surface
def drawCalendarSurface():
	# This panel is pasted 5px right of center,
	# thus x = 0 here is really center + 5px on main
	
	surfaceHeight = 274 	# remove 1px from height to not overwrite menu separator line
	surfaceWidth = 230		# remove 10px from width for padding on sides
	y = 0 					# Starting y axis
	
	calendarSurface = rightSideBaseSurface()
	
	todayHeader = False
	tomorrowHeader = False
	
	today = currentDate = datetime.date.today()
	tomorrow = today + datetime.timedelta(days = 1) 
	
	if len(calendar.data) == 0:
		calendarSurface.blit(smallFont.render("No calendar data", False, RGB_WHITE),(3, y + 3))
			
	else:
		# Loop through calendar events
		for event in calendar.data:
			
			# Check if end time has passed - Google calendar seems to have a delay
			# in removing past events from query.
			#end_time = dtparse(event['endTime'])
			#if event['allDay'] == True or end_time > datetime.datetime.now():

			# Get event date/time
			event_time = dtparse(event['dateTime'])
				
			# Today's items
			if event_time.date() == today:
				if not todayHeader:
					headerText = "Today"
					todayHeader = True
					newSection = False
				else:
					headerText = None
					
			# Tomorrow's items
			elif event_time.date() == tomorrow:
				if not tomorrowHeader:
					headerText = "Tomorrow"
					tomorrowHeader = True
					newSection = True
				else:
					headerText = None
				
			# Upcoming items
			else:
				if event_time.date() != currentDate:
					currentDate = event_time.date()
					headerText = datetime.datetime.strftime(event_time, "%a %b %d")
					newSection = True
				else:
					headerText = None
			
			# Generate time/summary string
			if event['allDay'] == True:
				s = u'\u2022' + ' ' + event['summary']
			else:
				s = u'\u2022' + ' ' + datetime.datetime.strftime(event_time, "%I:%M %p: ") + event['summary']
			
			# Box is taller than should be needed, but just to be safe
			box = pygame.Surface((surfaceWidth,surfaceHeight),pygame.SRCALPHA)
			rect = box.get_rect()
			textBox,accumulatedHeight = multiLineSurface(s, newsFont, rect, convertCalendarColor(event['color']), None, 1)
			
			if headerText:
				accumulatedHeight += smallFont.size(headerText)[1] + 3
			
			if accumulatedHeight + (6 if newSection else 0) <= (surfaceHeight - y):
				if headerText:
					# add a little padding above lines for new sections
					if newSection:
						y += 5
						
					# Draw line above header (only if not the first article)
					if y > 0:
						pygame.draw.line(calendarSurface, RGB_GRAY, (0,y), (surfaceWidth,y))
					
					day_icon = './graphics/calendar/' + str(event_time.day) + '.png'
					calendarSurface.blit(pygame.image.load(day_icon),(1, y+5))
					
					header = smallFont.render(headerText, False, RGB_WHITE)	
					headerWidth = header.get_width()
					
					x = surfaceWidth // 2 - headerWidth // 2
					calendarSurface.blit(header,(x, y + 4))
					
					y += smallFont.size(headerText)[1] + 5
				
				#Time & Summary
				calendarSurface.blit(textBox,(0, y))
				
				# advance y axis - any header spacing (y advances already within header section)
				y += accumulatedHeight + 2 - (smallFont.size(headerText)[1]+2 if headerText else 0)
			else:
				break
				
	return calendarSurface




def display_time(seconds, granularity=3):
	#https://stackoverflow.com/questions/4048651/python-function-to-convert-seconds-into-minutes-hours-and-days
    intervals = (
		('d', 86400),    # 60 * 60 * 24
		('h', 3600),    # 60 * 60
		('m', 60),
		)
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{:.0f}{}".format(value, name))
        else:
			result.append("0{}".format(name))
			
    return ' '.join(result[:granularity])


# Create surface for Pi Hole Data
def drawPiHoleSurface():
	surfaceHeight = 274 	# remove 1px from height to not overwrite menu separator line
	surfaceWidth = 230		# remove 10px from width for padding on sides
	y = 5 					# Starting y axis
	
	piholeSurface = rightSideBaseSurface()
	# Header / Logo
	piholeSurface.blit(pygame.image.load('./graphics/pihole_header.png'),(0, y))
	
	# Status
	if pihole.piholedata['status'] == 'enabled':
		text = 'Active'
	else:
		text = pihole.piholedata['status']
	text = newsFont.render(text, False, RGB_WHITE)
	
	# Status Circle
	headerEnd = 160
	x = headerEnd + (((surfaceWidth - headerEnd) // 2) - (text.get_width() // 2))
	piholeSurface.blit(text,(x, y+7))
	x = headerEnd + ((surfaceWidth - headerEnd) // 2)
	if pihole.piholedata['status'] == 'enabled':
		circleColor = RGB_GREEN
	else:
		circleColor = RGB_RED
	pygame.draw.circle(piholeSurface, circleColor, (x, y+34), 6)
	
	# Divider line
	y += 50
	pygame.draw.line(piholeSurface, RGB_GRAY, (5,y), (surfaceWidth-5,y))
	
	# Ads blocked today text
	y += 8
	s = "Ads Blocked Today: {0:.0f}%".format(pihole.piholedata['ads_percentage_today'])
	s = newsFont.render(s, False, RGB_WHITE)
	x = surfaceWidth // 2 - s.get_width() // 2
	piholeSurface.blit(s,(x, y))
	
	# Ads blocked today line graph
	y += 25
	left = x
	right = surfaceWidth-left
	xDivider = round(left + ((right - left) * (pihole.piholedata['ads_percentage_today'])/100))
	#pygame.draw.rect(screen, color, (x,y,width,height), thickness) 
	pygame.draw.rect(piholeSurface, RGB_RED, (left,y,xDivider-left,5))
	pygame.draw.rect(piholeSurface, RGB_GREEN, (xDivider,y,right-xDivider,5))
	pygame.draw.line(piholeSurface, RGB_GRAY, (5,y+15), (surfaceWidth-5,y+15))
	
	# Host name
	y += 23
	piholeSurface.blit(newsFont.render("Host:", False, RGB_WHITE),(10, y))
	s = newsFont.render(pihole.raspidata['host'], False, RGB_WHITE)
	x = surfaceWidth - 10 - s.get_width()
	piholeSurface.blit(s,(x, y))
	
	# IP Address
	y += 20
	piholeSurface.blit(newsFont.render("IP:", False, RGB_WHITE),(10, y))
	s = newsFont.render(pihole.raspidata['ip'], False, RGB_WHITE)
	x = surfaceWidth - 10 - s.get_width()
	piholeSurface.blit(s,(x, y))
	
	# Pi Uptime
	y += 20
	piholeSurface.blit(newsFont.render("Pi Uptime:", False, RGB_WHITE),(10, y))
	s = newsFont.render(pihole.raspidata['pi_uptime'], False, RGB_WHITE)
	x = surfaceWidth - 10 - s.get_width()
	piholeSurface.blit(s,(x, y))
	
	# Script Uptime
	y += 20
	piholeSurface.blit(newsFont.render("Script Uptime:", False, RGB_WHITE),(10, y))
	script_time = display_time(time.time() - scriptStartTime)
	#s = str(time)
	s = newsFont.render(script_time, False, RGB_WHITE)
	x = surfaceWidth - 10 - s.get_width()
	piholeSurface.blit(s,(x, y))
	
	# Clients
	y += 20
	piholeSurface.blit(newsFont.render("Clients:", False, RGB_WHITE),(10, y))
	s = newsFont.render(str(pihole.piholedata['unique_clients']), False, RGB_WHITE)
	x = surfaceWidth - 10 - s.get_width()
	piholeSurface.blit(s,(x, y))
	pygame.draw.line(piholeSurface, RGB_GRAY, (5,y+25), (surfaceWidth-5,y+25))
	
	# Memory Usage
	y = 221
	s = "Mem: {}%\n{}/{} MB".format(pihole.raspidata['memoryPercent'],pihole.raspidata['memoryUsed'],pihole.raspidata['memoryTotal'])
	box = pygame.Surface((surfaceWidth//2,100),pygame.SRCALPHA)
	rect = box.get_rect()
	textBox,accumulatedHeight = multiLineSurface(s, newsFont, rect, RGB_WHITE, None, 1)
	piholeSurface.blit(textBox,(0, y))
	
	pygame.draw.line(piholeSurface, RGB_GRAY, (120,y), (120,surfaceHeight-5))

	# Memory Usage line graph
	left = 10
	right = 110
	xDivider = round(left + ((right - left) * (float(pihole.raspidata['memoryPercent'])/100)))
	pygame.draw.rect(piholeSurface, RGB_RED, (left,y+40,xDivider-left,5))
	pygame.draw.rect(piholeSurface, RGB_GREEN, (xDivider,y+40,right-xDivider,5))
	
	# Disk Usage
	s = "Disk: {}%\n{}/{} GB".format(pihole.raspidata['diskPercent'],pihole.raspidata['diskUsed'],pihole.raspidata['diskTotal'])
	box = pygame.Surface((surfaceWidth//2,100),pygame.SRCALPHA)
	rect = box.get_rect()
	textBox,accumulatedHeight = multiLineSurface(s, newsFont, rect, RGB_WHITE, None, 1)
	piholeSurface.blit(textBox,(120, y))
	
	# Disk Usage line graph
	left = 130
	right = 220
	xDivider = round(left + ((right - left) * (float(pihole.raspidata['diskPercent'])/100)))
	pygame.draw.rect(piholeSurface, RGB_RED, (left,y+40,xDivider-left,5))
	pygame.draw.rect(piholeSurface, RGB_GREEN, (xDivider,y+40,right-xDivider,5))
	
	return piholeSurface
	
	
# Create a blank surface with only the given text
def drawBlankPanelWithText(text):
	blankSurface = rightSideBaseSurface()
	blankSurface.blit(smallFont.render(text, False, RGB_WHITE),(3,3))
	return blankSurface
	
	
	
def drawMenuSurface():
	surfaceHeight = 320
	surfaceWidth = 480
	menuSurface = pygame.Surface((surfaceWidth, surfaceHeight),pygame.SRCALPHA)
	menuSurface.blit(backgroundSurface, (0,0))
	pygame.draw.line(menuSurface, RGB_GRAY, (240,5), (240,surfaceHeight-5))
	
	##################
	# Left Side
	##################
	y = 10
	x = 5
	steps = 50
	linePadding = 45
	lines = False
	text_x_padding = 50
	text_y_padding = 5
	
	# Back Button
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/back.png'), (x,y))
	menuSurface.blit(dateFont.render("Back", False, RGB_WHITE), (x+text_x_padding,y+text_y_padding))
	if lines:
		pygame.draw.line(menuSurface, RGB_GRAY, (10,y+linePadding), (230,y+linePadding))
		menuSurface.blit(tinyFont.render(str(y+linePadding), False, RGB_WHITE), (0,y+linePadding))
	y += steps
	
	# Reboot
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/reboot.png'), (x,y))
	menuSurface.blit(dateFont.render("Reboot Pi", False, RGB_WHITE), (x+text_x_padding,y+text_y_padding))
	if lines:
		pygame.draw.line(menuSurface, RGB_GRAY, (10,y+linePadding), (230,y+linePadding))
		menuSurface.blit(tinyFont.render(str(y+linePadding), False, RGB_WHITE), (0,y+linePadding))
	y += steps
	
	# Shut down
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/power.png'), (x,y))
	menuSurface.blit(dateFont.render("Shutdown Pi", False, RGB_WHITE), (x+text_x_padding,y+text_y_padding))
	if lines:
		pygame.draw.line(menuSurface, RGB_GRAY, (10,y+linePadding), (230,y+linePadding))
		menuSurface.blit(tinyFont.render(str(y+linePadding), False, RGB_WHITE), (0,y+linePadding))
	y += steps
	
	# Screen saver
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/screenSaver.png'), (x,y))
	menuSurface.blit(dateFont.render("Screensaver", False, RGB_WHITE), (x+text_x_padding,y+text_y_padding))
	if lines:
		pygame.draw.line(menuSurface, RGB_GRAY, (10,y+linePadding), (230,y+linePadding))
		menuSurface.blit(tinyFont.render(str(y+linePadding), False, RGB_WHITE), (0,y+linePadding))
	y += steps
	
	# Go to sleep
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/sleep.png'), (x,y))
	menuSurface.blit(dateFont.render("Sleep Mode", False, RGB_WHITE), (x+text_x_padding,y+text_y_padding))
	if lines:
		pygame.draw.line(menuSurface, RGB_GRAY, (10,y+linePadding), (230,y+linePadding))
		menuSurface.blit(tinyFont.render(str(y+linePadding), False, RGB_WHITE), (0,y+linePadding))
	y += steps
	
	# Auto sleep
	if AUTO_SLEEP:
		menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/on.png'), (x,y))
	else:
		menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/off.png'), (x,y))
	menuSurface.blit(dateFont.render("Auto Sleep", False, RGB_WHITE), (x+text_x_padding,y+text_y_padding))
	
	
	##################
	# Right Side
	##################
	y = 0
	textPadding = 40
	sectionPadding = 53
	
	# Icons 8
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/icons8.png'), (340,y))
	text = "Icons by Icons8"
	text += "\nicons8.com"
	box = pygame.Surface((220,100),pygame.SRCALPHA)
	rect = box.get_rect()
	textBox,textHeight = multiLineSurface(text, newsFont, rect, RGB_WHITE, None, 1)
	menuSurface.blit(textBox, (250,y+textPadding))
	y += textHeight + sectionPadding - 5
	
	# Dark Sky
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/darksky.png'), (338,y))
	text = "Weather data by Dark Sky"
	text += "\ndarksky.net"
	text += "\nRIP:2022"
	box = pygame.Surface((220,100),pygame.SRCALPHA)
	rect = box.get_rect()
	textBox,textHeight = multiLineSurface(text, newsFont, rect, RGB_WHITE, None, 1)
	menuSurface.blit(textBox, (250,y+textPadding))
	y += textHeight + sectionPadding
	
	# News API
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/newsapi.png'), (344,y))
	text = "News data by News API"
	text += "\nnewsapi.org"
	box = pygame.Surface((220,100),pygame.SRCALPHA)
	rect = box.get_rect()
	textBox,textHeight = multiLineSurface(text, newsFont, rect, RGB_WHITE, None, 1)
	menuSurface.blit(textBox, (250,y+textPadding))
	y += textHeight + sectionPadding
	
	menuSurface.blit(pygame.image.load('./graphics/main_menu_graphics/workspace.png'), (340,285))
	
	return menuSurface
	


def drawConfirmSurface(text):
	surfaceWidth = 250
	surfaceHeight = 150
	confirmSurface = pygame.Surface((surfaceWidth, surfaceHeight))
	confirmSurface.fill(RGB_GRAY)
	pygame.draw.rect(confirmSurface, RGB_BLACK, (2,2,surfaceWidth-4,surfaceHeight-4))
	text = "Are you sure you want to " + text + "?"
	box = pygame.Surface((surfaceWidth-20,surfaceHeight),pygame.SRCALPHA)
	rect = box.get_rect()
	textBox,textHeight = multiLineSurface(text, dateFont, rect, RGB_WHITE, None, 1)
	confirmSurface.blit(textBox, (10,17))
	pygame.draw.line(confirmSurface, RGB_GRAY, (5,surfaceHeight-50), (surfaceWidth-5,surfaceHeight-50))
	confirmSurface.blit(pygame.image.load('./graphics/main_menu_graphics/on.png'), (5,surfaceHeight-45))
	confirmSurface.blit(dateFont.render("Yes", False, RGB_WHITE), (55,surfaceHeight-35))
	confirmSurface.blit(pygame.image.load('./graphics/main_menu_graphics/off.png'), (surfaceWidth//2+5,surfaceHeight-45))
	confirmSurface.blit(dateFont.render("No", False, RGB_WHITE), (surfaceWidth//2+55,surfaceHeight-35))
	pygame.draw.line(confirmSurface, RGB_GRAY, (surfaceWidth//2,surfaceHeight-50), (surfaceWidth//2,surfaceHeight-5))
	return confirmSurface


# Draw a message box surface for the menu shutdown/reboot
def drawMsgBoxSurface(text):
	surfaceWidth = 250
	surfaceHeight = 150
	confirmSurface = pygame.Surface((surfaceWidth, surfaceHeight))
	confirmSurface.fill(RGB_GRAY)
	pygame.draw.rect(confirmSurface, RGB_BLACK, (2,2,surfaceWidth-4,surfaceHeight-4))
	text = "Please wait while the pi " + text + "."
	box = pygame.Surface((surfaceWidth-20,surfaceHeight),pygame.SRCALPHA)
	rect = box.get_rect()
	textBox,textHeight = multiLineSurface(text, dateFont, rect, RGB_WHITE, None, 1)
	confirmSurface.blit(textBox, (10,50))
	return confirmSurface
	

# Return a full screen surface with wallpaper, mid-screen line, top-right icon menu
def drawBaseSurface():
	baseSurface = pygame.Surface((screenWidth, screenHeight))
	baseSurface.blit(backgroundSurface,(0, 0))
	pygame.draw.line(baseSurface, RGB_GRAY, (240,5), (240,315))
	# Screen Selector Icons (Only ever draws once)
	baseSurface.blit(drawTopRightIcons(),(241,0))
	return baseSurface



# Create and return the appropriate right side panel
def drawRightSidePanel():
	if CURRENT_SCREEN == 1:
		return drawHourlyOutlook()
	elif CURRENT_SCREEN == 2:
		return drawDailyOutlook()
	elif CURRENT_SCREEN == 3:
		return drawNewsSurface()
	elif CURRENT_SCREEN == 4:
		return drawCalendarSurface()
	elif CURRENT_SCREEN == 5:
		return drawPiHoleSurface()
	else:
		return drawBlankPanelWithText("Selection Unavailable")

# Draw a full main surface
def drawFullSurface():
	# Create Surface
	newSurface = pygame.Surface((480,320))
	# Return a full screen surface with wallpaper, mid-screen line, top-right icon menu
	newSurface.blit(drawBaseSurface(),(0, 0))
	# Draw line under current screen icon
	newSurface.blit(drawIconUnderline(),(241,41))
	# Time / Date (Draws every time)
	newSurface.blit(drawClock(), (0,0))
	# Big current weather section
	newSurface.blit(drawCurrentWeather(), (0,83))
	# Bottom Utility Stats
	newSurface.blit(drawUtilityStats(), (0,285))
	# Draw right side panel
	newSurface.blit(drawRightSidePanel(), (245,46))
	return newSurface


def slideRightSidePanel(newSurface, (x,y)):
	#(245,46)
	surfaceHeight = 274 	# remove 1px from height to not overwrite menu separator line
	surfaceWidth = 230		# remove 10px from width for padding on sides
	combinedSurface = pygame.Surface((surfaceWidth, surfaceHeight))
	
	leftEdge = 0 #x #245
	rightEdge = surfaceWidth #x + surfaceWidth #475

	# Capture existing surface to slide out
	oldSurface = pygame.Surface((surfaceWidth, surfaceHeight))
	oldSurface.blit(mainSurface, (0,0), (x,y,surfaceWidth,surfaceHeight))
	
	if SLIDE_DIRECTION == "right": # Slide toward the right edge
		# Loop x accross screen 5 pixels at a time
		for middle in range(leftEdge+5, rightEdge+1, 5):
			
			# Crop new surface as it slides in from the left
			width = middle - leftEdge
			leftCroppedSurface = pygame.Surface((width, surfaceHeight))
			leftCroppedSurface.blit(newSurface, (0,0), (surfaceWidth-width,0,width,surfaceHeight))
			
			# Crop old surface as it slides out to the right
			width = rightEdge - middle
			rightCroppedSurface = pygame.Surface((width, surfaceHeight))
			rightCroppedSurface.blit(oldSurface, (0,0), (0,0,width,surfaceHeight))
			
			# Combine into new surface
			combinedSurface.fill(RGB_BLACK)
			combinedSurface.blit(leftCroppedSurface,(0,0))
			combinedSurface.blit(rightCroppedSurface,(middle,0))
			
			# Refresh screen
			mainSurface.blit(combinedSurface,(x,y))
			PITFT.refresh(mainSurface)
			clock.tick(FPS)
			
	else: # Slide toward the left edge
		# Loop x accross screen 4 pixels at a time
		for middle in range(rightEdge-5, leftEdge-1, -5):
			
			# Crop old surface as it slides out to the left
			width = middle - leftEdge
			leftCroppedSurface = pygame.Surface((width, surfaceHeight))
			leftCroppedSurface.blit(oldSurface, (0,0), (surfaceWidth-width,0,width,surfaceHeight))
			
			# Crop new surface as it slides in from the right
			width = rightEdge - middle
			rightCroppedSurface = pygame.Surface((width, surfaceHeight))
			rightCroppedSurface.blit(newSurface, (0,0), (0,0,width,surfaceHeight))
			
			# Combine into new surface
			combinedSurface.fill(RGB_BLACK)
			combinedSurface.blit(leftCroppedSurface,(0,0))
			combinedSurface.blit(rightCroppedSurface,(middle,0))
			
			# Refresh screen
			mainSurface.blit(combinedSurface,(x,y))
			PITFT.refresh(mainSurface)
			clock.tick(FPS)



# Slides the menu open to the right
def slideMenuOpen():
	menuSurface = drawMenuSurface()
	for rightEdge in range(0,480+1,15):
		mainSurface.blit(menuSurface, (0,0), (480-rightEdge,0,rightEdge,320))
		PITFT.refresh(mainSurface)
		clock.tick(FPS)



# Slides the menu closed to the left
def slideMenuClose():
	menuSurface = pygame.Surface((480,320))
	menuSurface.blit(mainSurface, (0,0))
	fullSurface = drawFullSurface()
	for rightEdge in range(480,-1,-15):
		mainSurface.blit(fullSurface, (0,0))
		mainSurface.blit(menuSurface, (0,0), (480-rightEdge,0,rightEdge,320))
		PITFT.refresh(mainSurface)
		clock.tick(FPS)




CURRENT_SCREEN = 1			# Start on screen one
NUM_SCREENS = 5				# Total number of screens
SCREEN_ROTATE = True		# Default to rotate ON
SCREEN_SAVER = False		# Default to screen_saver off
REDRAW = False				# Flag to trigger screen redraw of specific content
FULL_REDRAW = True			# Flag to trigger full screen redraw (when menu closes)
SHOW_MENU = False			# Flag to show menu on top of main surface
AUTO_SLEEP = True			# Flag to enable/disable auto-sleep mode
CONFIRM_REBOOT = False		# Flag to confirm reboot selection from menu
CONFIRM_SHUTDOWN = False	# Flag to confirm shutdown selection from menu
REBOOTING = False			# Flag to confirm reboot has been called
SHUTTING_DOWN = False		# Flag,to confirm shutdown has been called
SLIDE_DIRECTION = "left"	# Keeps track of which way to 'slide' the right side panels


if __name__ == '__main__':
	powerOffCheck = False	# Flag to trigger 'zzz' icon on clock panel
	lastPowerOffCheck = 0	# Timer for the automatic LCD_OFF function
	weatherRefreshTime = 0	# Timer for weather data refresh
	newsRefreshTime = 0		# Timer for news data refresh
	calRefreshTime = 0		# Timer for calendar data refresh
	utilRefreshTime = 0		# Timer for utility data refresh
	sleepRefreshTime = 0	# Timer for auto-sleep action
	newsShuffleTime = 0		# Timer for news data shuffle
	piholeRefreshTime = 0	# Timer for pi-hole data refresh
	menuTimeOut = 0			# Timer for auto-closing of menu due to no response
	
	scriptStartTime = time.time()	# Start time to calculate 'script uptime'
	rotateTime = time.time()		# Timer to control auto-rotating right side panels
	xSleep = ySleep = 0				# x, y coordinates used for screen saver
	
	news = newsDataClass()
	calendar = calendarDataClass()
	pihole = piholeDataClass()
	utilities = utilityDataClass()
	weather = weatherDataClass()
	
	mainSurface = pygame.Surface((screenWidth, screenHeight)) # Surface for drawing, which will pass to screenClass to write to screen
	backgroundSurface = pygame.Surface((screenWidth, screenHeight)) # Background image surface
	backgroundSurface.fill(RGB_BLACK)
	backgroundSurface.blit(pygame.image.load('./graphics/bg.png'),(0,0))
	
	# Start up screen and backlight control
	PITFT = screenClass()
	PITFT.backlightOn()
	# currently have removed the backlight control as I believe it was causing a 
	# high pitched noise out of the LCD which I couldn't handle
	#PITFT.backlightControlOn()
	#PITFT.backlightSetBrightness(PITFT.maxBrightness//2) # Max Brightness (0-1023)
	# Backlight startup variables
	# Backlight will gradually get brighter over the course of a half hour after the auto-off cutoff time
	
	
	try:
		while True:	
			# Set current time for clock functions
			now = datetime.datetime.now()
			
			#############################################################
			# Auto sleep mode between 4pm - 5am (Turns LCD Off)
			# Set against a timer, allowing user to 'wake' for 5 minutes
			#############################################################
			if AUTO_SLEEP:
				#if current time is greater than 4pm or less than 5am and LCD is still on
				if (now.hour >= 16 or now.hour < 5):
					if PITFT.screenOn:
						powerOffCheck = True
						# Start the time-out check if it's not already
						if PITFT.lastPowerOffCheck == 0:
							PITFT.lastPowerOffCheck = time.time()
							print "{} Automatic sleep mode check has started...".format(now.strftime("%I:%M:%S %p"))
						
						# If threshold has been met:
						if (time.time() - PITFT.lastPowerOffCheck) > (60 * 5): # 5 Minutes
							if PITFT.screenOn:
								print "{} Automatic sleep mode activated: Turning off LCD...".format(now.strftime("%I:%M:%S %p"))
								PITFT.backlightOff()
				else:
					powerOffCheck = False
					if not PITFT.screenOn:
						PITFT.backlightOn()
					
			else:
				powerOffCheck = False
				if not PITFT.screenOn:
					PITFT.backlightOn()
			
			
			# Only update and draw data if LCD is on
			if PITFT.screenOn:
				
				# Update Utility stats as all screens use this
				if (time.time() - utilities.lastUpdated) > 5: # 5 seconds
					utilities.updateData()


				#############################
				# Screen Saver
				#############################
				if SCREEN_SAVER:
					mainSurface.fill(RGB_BLACK)
					#https://stackoverflow.com/questions/42577197/pygame-how-to-correctly-use-get-rect
					box = pygame.Surface((230,65),pygame.SRCALPHA)
					rect = box.get_rect(topleft=(0,0))
					
					# Date/Time
					s = now.strftime("%a %b %d %I:%M %p")
					#s += '\n' + str(utilities.data['cpu']) + '  ' + str(utilities.data['rpiTemp'])
					s += '\nPress anywhere to resume'
					textBox,accumulatedHeight = multiLineSurface(s, smallFont, rect, RGB_GRAY, None, 1)
					mainSurface.blit(textBox, (xSleep,ySleep))
					
					# Move location every 5 seconds
					if (time.time() - sleepRefreshTime) > (5): # 5 Seconds
						xSleep = randint(0,480-rect.width)
						ySleep = randint(0,320-rect.height)
						sleepRefreshTime = time.time()
				
				#############################
				# Main Menu
				#############################
				elif SHOW_MENU:
					# Time out the menu after 30 seconds
					if menuTimeOut == 0:
						menuTimeOut = time.time()
					elif (time.time() - menuTimeOut) > 30:
							slideMenuClose()
							SHOW_MENU = False
							menuTimeOut = 0
							#mainSurface.blit(drawBaseSurface(),(0, 0))
					else:	
						#mainSurface.blit(drawMenuSurface(),(0,0))
						if CONFIRM_REBOOT:
							mainSurface.blit(drawConfirmSurface("reboot"),(115,85))
						elif CONFIRM_SHUTDOWN:
							mainSurface.blit(drawConfirmSurface("shutdown"),(115,85))
						elif REBOOTING:
							mainSurface.blit(drawMsgBoxSurface("reboots"),(115,85))
						elif SHUTTING_DOWN:
							mainSurface.blit(drawMsgBoxSurface("shuts down"),(115,85))
				#############################
				# Normal Screen
				#############################	
				else:
					if FULL_REDRAW:
						mainSurface.blit(drawBaseSurface(),(0, 0))
	
					# Rotate screen every 30 seconds
					if SCREEN_ROTATE:
						if (time.time() - rotateTime) > 30:
							if (CURRENT_SCREEN % NUM_SCREENS) + 1 < CURRENT_SCREEN:
								SLIDE_DIRECTION = "right"
							else:
								SLIDE_DIRECTION = "left"
							CURRENT_SCREEN = (CURRENT_SCREEN % NUM_SCREENS) + 1
							rotateTime = time.time()
							REDRAW = True
							
					# Check if weather needs updating
					if (time.time() - weather.lastUpdated) > (60 * 10): # 10 minutes
						if CURRENT_SCREEN == 1 or CURRENT_SCREEN == 2:
							# Put in 'updating' screen in case of slow update
							mainSurface.blit(drawBlankPanelWithText("Updating Weather Data..."),(245,46))
							mainSurface.blit(drawIconUnderline(),(241,41))
							PITFT.refresh(mainSurface)
						weather.updateData()
						REDRAW = True
					
					# Check for other data updates (Only update when page is in view to avoid all updates at once)
					# News Data
					if CURRENT_SCREEN == 3:
						# Check if news needs updating
						if (time.time() - news.lastUpdated) > (60 * 30): # 30 minutes
							# Put in 'updating' screen in case of slow update
							mainSurface.blit(drawBlankPanelWithText("Updating News Data..."),(245,46))
							mainSurface.blit(drawIconUnderline(),(241,41))
							PITFT.refresh(mainSurface)
							news.updateNews()
							REDRAW = True
						
						# Shuffle articles array every minute
						if (time.time() - news.lastShuffle) > 60:
							news.shuffleArticles()
							REDRAW = True
							
					# Calendar Data
					elif CURRENT_SCREEN == 4:
						if (time.time() - calendar.lastUpdated) > (60 * 60): # 60 minutes
							# Put in 'updating' screen in case of slow update
							mainSurface.blit(drawBlankPanelWithText("Updating Calendar Data..."),(245,46))
							mainSurface.blit(drawIconUnderline(),(241,41))
							PITFT.refresh(mainSurface)
							calendar.updateData()
							REDRAW = True
					
					# Pihole Data
					elif CURRENT_SCREEN == 5:
						if (time.time() - pihole.lastUpdated) > (60 * 15): # 15 minutes
							# Because this refresh is a bit slower, put in an updating screen otherwise,
							# it appears to be unresponsive
							mainSurface.blit(drawBlankPanelWithText("Updating Pi-Hole Data..."),(245,46))
							mainSurface.blit(drawIconUnderline(),(241,41))
							PITFT.refresh(mainSurface)
							pihole.updateData()
							REDRAW = True
							
							
					'''
					####################################
					#        LEFT SIDE PANEL           #
					####################################
					'''
					# Time / Date (Draws every time)
					mainSurface.blit(drawClock(), (0,0))
					
					# Big current weather section (Only draws when refreshed)
					if REDRAW or FULL_REDRAW:
						mainSurface.blit(drawCurrentWeather(), (0,83))
		
					# Bottom Utility Stats (Draws every time)
					mainSurface.blit(drawUtilityStats(), (0,285))

					'''
					####################################
					#        RIGHT SIDE PANEL          #
					####################################
					'''
					# Icon Underline
					if REDRAW or FULL_REDRAW:
						mainSurface.blit(drawIconUnderline(),(241,41))

					if REDRAW or FULL_REDRAW:
						slideRightSidePanel(drawRightSidePanel(),(245,46))
				
				
				# Write all updates to screen
				PITFT.refresh(mainSurface)
				REDRAW = FULL_REDRAW = False
			
			# check for screen touch to advance screens
			event = touch.read_one()
			if event: #for event in touch.read():
				if event.type == evdev.ecodes.EV_ABS:
					if event.code == 1:
						X = event.value
					elif event.code == 0:
						Y = event.value
				elif event.type == evdev.ecodes.EV_KEY:
					if event.code == 330 and event.value == 1:
						#printEvent(event)
						if X and Y:
							p = getPixelsFromCoordinates((X, Y))
							processTouch(p, PITFT)
						#print("{0} TFT: {1}:{2} | Pixels: {3}:{4}".format(datetime.datetime.now().strftime("%I:%M:%S %p"),X, Y, p[0], p[1]))
			
			clock.tick(FPS)
					
	except:
		mainSurface.fill(RGB_BLACK)
		PITFT.refresh(mainSurface)
		traceback.print_exc(file=sys.stdout)
		pygame.quit()
		exit()

