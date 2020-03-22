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
		
		spi_width = 16
		
		# Data registers
		data_in = Signal(spi_width)
		data_out = Signal(spi_width)
		
		# SPI slave
		spiSlave = SpiSlave(width=spi_width)
		m.submodules += spiSlave
		m.d.comb += data_in.eq(spiSlave.data_in)
		m.d.comb += spiSlave.data_out.eq(data_out)
		
		m.d.comb += data_out.eq(data_in) # Loopback
		
		spiConnector = platform.request("spi", 0)
		m.d.comb += spiSlave.spi_sclk.eq(spiConnector['sclk'].i)
		m.d.comb += spiSlave.spi_ssel.eq(spiConnector['ssel'].i)
		m.d.comb += spiSlave.spi_mosi.eq(spiConnector['mosi'].i)
		m.d.comb += spiConnector['miso'].o.eq(spiSlave.spi_miso)
		m.d.comb += spiConnector['miso'].oe.eq(~spiSlave.spi_ssel)
				
		# 14 segment display
		fourteenSegmentDisplay = FourteenSegmentDisplay()
		m.d.comb += fourteenSegmentDisplay.data.eq(spiSlave.data_in[0:7])
		m.submodules += fourteenSegmentDisplay
		
		# LEDs
		for i in range(8):
			led = platform.request("led", i)
			m.d.sync += led.o.eq(~spiSlave.data_in[8+i])
		
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
		Subsignal("miso", Pins("expcon_2:6", dir="io")), # Output is only driven when SSEL is low
		Attrs(IO_STANDARD="LVCMOS33")
	)])
	
	platform.build(Top(), build_dir=args.build_dir, do_program=True)
