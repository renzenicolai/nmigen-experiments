from nmigen import *
from nmigen.build import Platform, ResourceError, Resource, Subsignal, Pins, Attrs
from nmigen.cli import main

from nmigen_boards.versa_ecp5_5g import VersaECP55GPlatform

import argparse

from fourteensegmentdisplay import FourteenSegmentDisplay
from spi_slave import SpiSlave

class Top(Elaboratable):
	def __init__(self):
		pass

	def elaborate(self, platform: Platform) -> Module:
		m = Module()
		
		# Data registers
		data_in = Signal(8)
		
		# SPI slave
		spiSlave = SpiSlave()
		m.submodules += spiSlave
		m.d.comb += data_in.eq(spiSlave.data_in)
		
		spiConnector = platform.request("spi", 0)
		m.d.comb += spiSlave.spi_sclk.eq(spiConnector['sclk'].i)
		m.d.comb += spiSlave.spi_ssel.eq(spiConnector['ssel'].i)
		m.d.comb += spiSlave.spi_mosi.eq(spiConnector['mosi'].i)
		m.d.comb += spiConnector['miso'].o.eq(spiSlave.spi_miso)
		
		# LEDs
		for i in range(8):
			led = platform.request("led", i)
			m.d.sync += led.o.eq(~spiSlave.data_in[i])
				
		# 14 segment display
		fourteenSegmentDisplay = FourteenSegmentDisplay()
		m.d.comb += fourteenSegmentDisplay.data.eq(spiSlave.data_in)
		m.submodules += fourteenSegmentDisplay
		return m

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("build_dir")
	args = parser.parse_args()
	platform = VersaECP55GPlatform()
	
	# Extend platform with SPI connections
	platform.add_resources([Resource("spi", 0,
		Subsignal("sclk", Pins("expcon_2:3", dir="i")),
		Subsignal("ssel", Pins("expcon_2:4", dir="i")),
		Subsignal("mosi", Pins("expcon_2:5", dir="i")),
		Subsignal("miso", Pins("expcon_2:6", dir="o")),
		Attrs(IO_STANDARD="LVCMOS33")
	)])
	
	platform.build(Top(), build_dir=args.build_dir, do_program=True)
