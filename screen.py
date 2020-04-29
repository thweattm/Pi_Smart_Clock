import os
#import pygame

class screenClass(object):
	def __init__(self):
		self.lastPowerOffCheck = 0
		self.screenOn = True
		self.minBrightness = 0
		self.maxBrightness = 1023
		self.currentBrightness = 1023

	
	# Original on/off methods)
	def backlightOff(self):
		# https://learn.adafruit.com/adafruit-pitft-28-inch-resistive-touchscreen-display-raspberry-pi/backlight-control
		os.popen("sudo sh -c 'echo \"0\" > /sys/class/backlight/soc\:backlight/brightness'")
		self.screenOn = False
	def backlightOn(self):
		os.popen("sudo sh -c 'echo \"1\" > /sys/class/backlight/soc\:backlight/brightness'")
		self.screenOn = True
		self.lastPowerOffCheck = 0
	
	''' While these did work, I believe it was causing a high pitched noise from the screen which I couldn't handle
	#Newer methods to enable the gpio mode on pin 18 -- doesn't seem necessary every time
	#https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/faq?view=all#backlight-control
	def backlightControlOn(self):
		os.popen("sudo sh -c 'echo \"0\" > /sys/class/backlight/soc\:backlight/brightness'")
		os.popen("gpio -g mode 18 pwm")
		os.popen("gpio pwmc 1000")
	
	# For this to work, the backlightOff command above (old method) would have already need to be run
	def backlightSetBrightness(self,brightness):
		self.currentBrightness = brightness
		cmd = "gpio -g pwm 18 {}".format(self.currentBrightness)
		os.popen(cmd)
		if brightness > 0:
			self.screenOn = True
		else:
			self.screenOn = False
		
	def backlightOn(self):
		if self.currentBrightness == 0:
			self.currentBrightness = self.maxBrightness
		cmd = "gpio -g pwm 18 {}".format(self.currentBrightness)
		os.popen(cmd)
		self.screenOn = True
	
	def backlightOff(self):
		os.popen("gpio -g pwm 18 0")
		self.screenOn = False
	'''
	
	# Helper to write pygame 'screen' to frame buffer
	def refresh(self, baseSurface):
		f = open("/dev/fb1","wb")
		f.write(baseSurface.convert(16,0).get_buffer())
		f.close()
		
	def shutdown(self):
		os.popen("sudo shutdown -h now") # "sudo halt"
		
	def reboot(self):
		os.popen("sudo shutdown -r now") # "sudo reboot"
