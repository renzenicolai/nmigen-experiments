from machine import SPI, Pin
import time

ssel = Pin(18, Pin.OUT)
ssel.value(1)

spi = SPI(1, baudrate=20000000, bits=8, sck=Pin(5, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(4, Pin.IN))

time.sleep(0.1)

string = "HELLO WORLD, THIS IS A TEST    0123456789    "

while True:
	for i in range(len(string)):
		ssel.value(0); spi.write(bytes([ord(string[i])])); ssel.value(1)
		time.sleep(0.1)
