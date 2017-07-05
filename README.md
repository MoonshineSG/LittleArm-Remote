## Little Arm bluetooth remote control


### Components
![screenshot](https://moonshinesg.github.io/images/littlearm/1.jpg)

- PyBoard (https://store.micropython.org/#/products/PYBv1_1) 
- PyBoard skin (https://store.micropython.org/#/products/PROTOSKIN-PTXYv1_0)
- 4 momentary SPDT switches
- 3 momentary NO switches
- 1 variable resistor
- 5V buzzer (for audio feedback)
- 5V power bank 
- HC-05 bluetooth module (paired as master / slave with the HC-05 on the LittleArm)

### Schematics
![screenshot](https://moonshinesg.github.io/images/littlearm/0.png)

### Assembled
![screenshot](https://moonshinesg.github.io/images/littlearm/2.jpg)

### 3D model enclosure (fusion 360)
![screenshot](https://moonshinesg.github.io/images/littlearm/3.png)

The print came out quite bad. (maybe one day it will be printed again)

### Power source (hot glue fixed)
![screenshot](https://moonshinesg.github.io/images/littlearm/4.jpg)

### All fitted in the box
![screenshot](https://moonshinesg.github.io/images/littlearm/5.jpg)

### Ready
![screenshot](https://moonshinesg.github.io/images/littlearm/6.jpg)

- Yellow - speed control
- Blue - home position (hardcoded)
- Red -  record position

	insert "pause" if speed set to 0

- Green - Playback / Stop Playback	
	
	the sequence will playback at recorded speed (for individual step) when speed control set to 0, or at speed control value if anything else is selected
	
	press Red & Green together to reset playback sequence

- 4 "up/down" controls (rotation, 2 arms and grip)

### Power on!
![screenshot](https://moonshinesg.github.io/images/littlearm/7.jpg)
