from machine import SPI, Pin
import time

# SPI bus init
ssel = Pin(18, Pin.OUT)
ssel.value(1)
spi = SPI(1, baudrate=20000000, bits=8, sck=Pin(5, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(4, Pin.IN), firstbit=SPI.MSB)

# Write function
def writeByte(b):
	ssel.value(0) # Select FPGA SPI device
	spi.write(bytes([b])) # Send data to FPGA
	ssel.value(1) # De-select FPGA SPI device

def writeChar(c):
	writeByte(ord(c))

# Test
text = "HELLO WORLD"

while True:
	for i in range(len(text)):
		writeChar(text[i])
		time.sleep(0.1)
	
	for i in range(0x100):
		writeByte(i)
		time.sleep(0.1)
	
	for i in range(0x100):
		writeByte(i)
		time.sleep(0.01)
