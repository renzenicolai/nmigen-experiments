from machine import SPI, Pin
import time

# SPI bus init
ssel = Pin(18, Pin.OUT)
ssel.value(1)
spi = SPI(1, baudrate=20000000, bits=8, sck=Pin(5, Pin.OUT), mosi=Pin(19, Pin.OUT), miso=Pin(4, Pin.IN), firstbit=SPI.MSB)

# Write function
def transaction(tx):
	ssel.value(False) # Select FPGA SPI device
	rx = bytearray([0]*len(tx))
	spi.write_readinto(tx, rx)
	ssel.value(True) # De-select FPGA SPI device
	return rx

def runTest(val):
	data = None
	for i in range(16):#0x100):
		prevData = data
		led = 1<<(i%8) if not (i>>3)&1 else 1<<(7-i%8)
		data = bytearray([led,val])
		result = transaction(data)
		if prevData and not result == prevData:
			print("Test failed, expected {} got {}.".format(prevData, result))
			return False
		time.sleep(0.01)
		first = False
	return True

tests = 0
failed = 0
while True:
	if not runTest(ord("{}".format(tests)[-1])):
		failed += 1
	tests += 1
	print("Tests run {}, failed {}".format(tests, failed))
