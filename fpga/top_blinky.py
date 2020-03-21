from nmigen import *
from nmigen.build import Platform, ResourceError
from nmigen.cli import main

from nmigen_boards.versa_ecp5_5g import VersaECP55GPlatform

import argparse

from fourteensegmentdisplay import FourteenSegmentDisplay

class Blinky(Elaboratable):
	def __init__(self):
		pass

	def elaborate(self, platform: Platform) -> Module:
		m = Module()
		
		#100MHz clock signal
		clk100 = ClockSignal("clk100")
		m.d.comb += clk100.eq(platform.request("clk100").i)
		#m.domains += clk100
		
		# Counter
		clk_freq = platform.default_clk_frequency
		self.counter = Signal(range(int(clk_freq//8)))
		m.d.clk100 += self.counter.eq(self.counter + 1)
		
		# Text
		msg = "     HELLO BADGE.TEAM  THIS IS A TEST OF THE 14 SEGMENT DISPLAY ON THE LATTICE ECP5 VERSA BOARD."
		
		# Slow counter A
		self.slowCounterA = Signal(8, reset=0)
		with m.If(self.counter == 0):
			with m.If(self.slowCounterA < len(msg)):
				m.d.clk100 += self.slowCounterA.eq(self.slowCounterA + 1)
			with m.Else():
				m.d.clk100 += self.slowCounterA.eq(0)
		
		# Normal LEDs
		i = 0
		while True:
			try:
				led = platform.request("led", i)
				m.d.comb += led.o.eq(~self.slowCounterA[-1-i])
				i+=1
			except ResourceError:
				break
		
		# Segment LEDs
		fourteenSegmentDisplay = FourteenSegmentDisplay()
		with m.Switch(self.slowCounterA):
			for i in range(len(msg)):
				with m.Case(i+1):
					m.d.comb += fourteenSegmentDisplay.data.eq(ord(msg[i]))
			with m.Default():
				m.d.comb += fourteenSegmentDisplay.data.eq(0xFF)
		m.submodules += fourteenSegmentDisplay
		
		# Clock domain
		m.domains += ClockDomain("clk100")
		return m

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("build_dir")
	args = parser.parse_args()
	VersaECP55GPlatform().build(Blinky(), build_dir=args.build_dir, do_program=True)
