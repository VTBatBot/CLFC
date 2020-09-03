import RPi.GPIO as GPIO

# Pin definitions - correspond to the BOARD numbers for the select and enable pins 
# that are defined in the documentation for the multi camera v2.2
pin_selector = 7
pin_enable1 = 26
pin_enable2 = 19

#Board mode means that the numbers provided for pins correspond to the number of the pin on the board, i.e. pin 1 in this code is pin 1 on the Jetson's pin header - pretty straightforward!
GPIO.setmode(GPIO.BOARD)

#Set all pins to be outputs. Start all pins in the 'all cameras off' position (All pins high)
GPIO.setup(pin_selector, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(pin_enable1, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(pin_enable2, GPIO.OUT, initial=GPIO.HIGH)

#Camera A's config is (Sel, EN1, EN2) = (0,1,0)
def select_camera_A():
	all_pins_off()
	GPIO.output(pin_selector, GPIO.LOW)
	GPIO.output(pin_enable1, GPIO.LOW)

#Camera A's config is (Sel, EN1, EN2) = (0,1,0)
def select_camera_B():
	all_pins_off()
	GPIO.output(pin_enable1, GPIO.LOW)

#Camera A's config is (Sel, EN1, EN2) = (0,1,0)
def select_camera_C():
	all_pins_off()
	GPIO.output(pin_selector, GPIO.LOW)
	GPIO.output(pin_enable2, GPIO.LOW)

#Camera A's config is (Sel, EN1, EN2) = (0,1,0)
def select_camera_D():
	all_pins_off()
	GPIO.output(pin_enable2, GPIO.LOW)

#Turn all cameras off
def all_pins_off()
	GPIO.output(pin_selector, GPIO.HIGH)
	GPIO.output(pin_enable1, GPIO.HIGH)
	GPIO.output(pin_enable2, GPIO.HIGH)

def close_down()
	GPIO.cleanup()
	return
