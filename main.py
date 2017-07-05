import micropython, pyb
from pyb import Pin, ADC, UART, Timer
import time
import random
import os
from buzzer import *

micropython.alloc_emergency_exception_buf(1000)

#comunication
serial = UART(3, 38400)


#pin definition
pin_base_left = Pin('Y1', Pin.IN, Pin.PULL_DOWN)
pin_base_right = Pin('Y2', Pin.IN, Pin.PULL_DOWN)

pin_shoulder_up = Pin('Y3', Pin.IN, Pin.PULL_DOWN)
pin_shoulder_down = Pin('Y4', Pin.IN, Pin.PULL_DOWN)

pin_elbow_up = Pin('Y5', Pin.IN, Pin.PULL_DOWN)
pin_elbow_down = Pin('Y6', Pin.IN, Pin.PULL_DOWN)

pin_grip_open = Pin('Y7', Pin.IN, Pin.PULL_DOWN)
pin_grip_close = Pin('Y8', Pin.IN, Pin.PULL_DOWN)

pin_home = Pin('X5', Pin.IN, Pin.PULL_DOWN)

pin_save = Pin('X6', Pin.IN, Pin.PULL_DOWN)
pin_play = Pin('X7', Pin.IN, Pin.PULL_DOWN)

pin_speed = ADC(Pin('X12'))

buzzer = Buzzer("X1")

#global variables
prev_position = None #keep track of the save position
playback = False #is playing a sequence ? 
ready = True #do we need to read the buttons ? (or we are waiting for a response ?)

#sounds
tone_init = [(G5, 120),(C8,120)]
tone_start = [(A6, 150),(B6,120),(C7, 120),(G7,150),(A7, 120),(B7,120),(C8,150)]
tone_home  = [(G7,80), (A5,180), (G7,150),(B7,100)]
tone_play  = [(D8,170)]
tone_stop  = [(D8, 80), (DS8, 12)]
tone_reset = [(D8, 130), (0, 50),  (A6, 120), (G7, 80)]
tone_cancel = [(C7, 100), (CS7, 100), (D7, 100), (DS7, 100)]
tone_done  = [(C5, 100)]
tone_error = [(C8, 100), (0, 50), (B5, 100)]
tone_save  = [(G6, 110), (G6, 110)]

#util functions

#checks if file exists
def exists(fname):
	try:
		with open(fname):
			pass
		return True
	except OSError:
		return False

#https://stackoverflow.com/questions/1630320/what-is-the-pythonic-way-to-detect-the-last-element-in-a-python-for-loop
def lookahead(iterable):
	"""Pass through all values from the given iterable, augmented by the
	information if there are more values to come after the current one
	(True), or if it is the last value (False).
	"""
	# Get an iterator and pull the first value.
	it = iter(iterable)
	last = next(it)
	# Run the iterator to exhaustion (starting from the second value).
	for val in it:
		# Report the *previous* value (more to come).
		yield last, True
		last = val
	# Report the last value.
	yield last, False

#arduino style map
def arduino_map(x, in_min, in_max, out_min, out_max):
  return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

#make some noise
def alert(sound):
	for note in sound:
		buzzer.buzz(note[0], note[1])
	buzzer.buzz(0, 10) #short pause (10ms)
	
#output functions	
def write(data):
	sequence = []
	if exists('sequence.txt'):
		with open('sequence.txt') as the_file:
			sequence = the_file.readlines()
	sequence.append(data+'\n')	
	the_file = open('sequence.txt', 'w')
	for line in sequence:
		the_file.write(line)
		print("sequence ["+ line.strip() +"]")
	the_file.close()
	
	pyb.sync() #important!!

#erase 
def reset():
	if exists('sequence.txt'):
		os.remove('sequence.txt')
		pyb.sync()
		alert(tone_reset)

#wrap data and send it 
def send_data(data):
	#print("Sendig: [" + str(data) + "]")
	serial.write( "<" + str(data) + ">")

#read the ADC and convert 
def get_speed():
	#map the values from (almost) MIN to (almost0 MAX (ADC amx read = 4095) in 100 steps
	return str(arduino_map(pin_speed.read(), 5, 4090, 0, 100)) 
 
#go to predifined position
def home():
	if get_speed() == "0":
		alert(tone_error)
	else:
		send_data("A:90,45,179,10,"+get_speed())
		alert(tone_home)

#play the saved positions in a continuous loop	
def play():
	global playback	
	if exists('sequence.txt'):
		alert(tone_play)
		the_file = open('sequence.txt', 'r')
		content = the_file.readlines()
		the_file.close()		
		#for command in content:
		while 1:
			for command, has_more in lookahead(content):
				
				if get_speed() != "0": #speed dial is set to 0
					send_data("A:" + command.strip()) #send unmodified sequence
				else:
					cmd, spd = command.strip().rsplit(',',1)
					if spd == "0":
						send_data("A:0,0,0,0,0") #pause
					else:
						send_data("A:" + cmd + "," + get_speed()) #send with read speed 

				if has_more: #is it last one ? 
					if not wait_next_response():
						alert(tone_cancel)
						playback = False
						return
				else:
					alert(tone_done)
					if pin_play.value(): #cancel
						playback = False
						return
					send_data("A:0,0,0,0,0") #pause
	else:
		alert(tone_error)
	playback = False

#input functions
def wait_next_response():
	while True:
		time.sleep(0.1)
		if pin_play.value(): #cancel
			return False
		if serial.any():
			data = serial.readline().decode("utf-8").strip()
			#print("<< "+data)
			if data.startswith("A:N"):
				time.sleep(0.2) #tiny pause between playback commands
				return True
			elif data.startswith("started"):
				#print("started")
				alert(tone_start)
				return False

def read_data():
	global prev_position, ready
	if serial.any():
		data = serial.readline().decode("utf-8").strip()
		#print("<< "+data)
		if data.startswith("P:"):
			if prev_position != data:
				alert(tone_save)
				prev_position = data
				write( data[2:] + "," + get_speed() )
		elif data.startswith("R:D"):
			ready = True
		elif data.startswith("started"):
			#print("started")
			alert(tone_start)
			ready = True
			playback = False
			

#we started
alert(tone_init)

#wait for a few sec for the bluetooth to connect
time.sleep(5) 

#ask for "started"
send_data("C:") 

#main loop
while True:
	
	if not playback: #only if we dont play a sequence - see: play()
	
		#read received data
		read_data()

		#get pins values
		base = None
		shoulder = None
		elbow = None
		grip = None
		
		if pin_base_left.value():
			base = "1"
		elif pin_base_right.value():
			base = "2"

		if pin_shoulder_up.value():
			shoulder = "1"
		elif pin_shoulder_down.value():
			shoulder = "2"

		if pin_elbow_up.value():
			elbow = "1"
		elif pin_elbow_down.value():
			elbow = "2"

		if pin_grip_open.value():
			grip = "1"
		elif pin_grip_close.value():
			grip = "2"

		if base or shoulder or elbow or grip : #at least one button is pushed
			if ready:
				if get_speed() == "0":
					alert(tone_error)
				else:
					#0 for buttons not pressed
					data = (base or "0") + "," + (shoulder or "0") + "," +  (elbow or "0") + "," + (grip or "0") 
					send_data("R:" + data + "," + get_speed())
					ready = False

		else: #check other pins

			#check Home pin
			if pin_home.value():
				print("home!")
				home()
			elif pin_play.value() and pin_save.value():  #both buttons are pushed
				print("reset")
				reset()
			elif pin_play.value():
				print("play")
				playback = True
				play()
			elif pin_save.value():
				print("save")
				send_data("P:")	#querry position
			time.sleep(0.1)
