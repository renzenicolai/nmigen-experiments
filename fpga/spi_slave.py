from nmigen import *
from nmigen.build import Platform, ResourceError
from nmigen.back.pysim import Simulator, Delay, Settle

class SpiSlave(Elaboratable):
	def __init__(self, simulation = False, lsbFirst = False):
		# Signals in system clock domain
		self.data_out = Signal(8)     # Data to be sent during next SPI transaction
		self.data_in  = Signal(8)     # Data received from SPI during last transaction
		self.counter  = Signal(4)     # Counter showing the amount of bits received
		
		# Signals in SPI clock domain
		self.spi_sclk = Signal(1) # SPI clock
		self.spi_ssel = Signal(1) # SPI slave select
		self.spi_mosi = Signal(1) # SPI master out slave in
		self.spi_miso = Signal(1) # SPI master in slave out
		
		# Simulation flag
		self._simulation = simulation
		
		# Settings
		self.lsbFirst = lsbFirst
	
	def elaborate(self, platform: Platform) -> Module:
		m = Module()
		
		# Sampled SPI clock signal
		sclk_reg = Signal(3)
		m.d.sync += sclk_reg.eq((sclk_reg<<1) | self.spi_sclk)
		
		# Edge detection on sampled SPI clock signal
		sclk_risingedge = Signal(1)
		m.d.comb += sclk_risingedge.eq(sclk_reg[1:3]==0b01)
		
		sclk_fallingedge = Signal(1)
		m.d.comb += sclk_fallingedge.eq(sclk_reg[1:3]==0b10)
		
		# Sampled SPI slave select signal
		ssel_reg = Signal(3)
		m.d.sync += ssel_reg.eq((ssel_reg<<1) | self.spi_ssel)
		
		ssel_active = Signal(1)
		m.d.sync += ssel_active.eq(~ssel_reg[1])
		
		# Edge detection on sampled SPI slave select signal
		ssel_risingedge = Signal(1) # (Signals start of message)
		m.d.comb += ssel_risingedge.eq(ssel_reg[1:3]==0b01)
		
		ssel_fallingedge = Signal(1) # (Signals end of message)
		m.d.comb += ssel_fallingedge.eq(ssel_reg[1:3]==0b10)
		
		# Sampled SPI master out slave in signal
		mosi_reg = Signal(2)
		m.d.sync += mosi_reg.eq((mosi_reg[0]<<1) | self.spi_mosi)
		
		mosi = Signal(1)
		m.d.comb += mosi.eq(mosi_reg[1])
		
		# Buffers
		tx_buffer = Signal(8)
		rx_buffer = Signal(8)
		
		# Data output
		m.d.comb += self.spi_miso.eq(tx_buffer[0])
		
		# Transaction state machine
		with m.If(~ssel_active): # We are not selected, reset state
			m.d.sync += self.counter.eq(0)
		with m.Elif(sclk_risingedge): # Clock ticked, read data
			m.d.sync += self.counter.eq(self.counter+1)
			if self.lsbFirst:
				m.d.sync += rx_buffer.eq((rx_buffer>>1) | (mosi<<7))
			else:
				m.d.sync += rx_buffer.eq((rx_buffer<<1) | mosi)
		
		with m.If(ssel_risingedge): # End of transaction
			m.d.sync += tx_buffer.eq(self.data_out)
			m.d.sync += self.data_in.eq(rx_buffer)
		with m.Elif(sclk_fallingedge): # Clock ticked, write data
			m.d.sync += tx_buffer.eq(tx_buffer>>1)
		
		# Expose internal signals during simulation
		if self._simulation:
			self._ssel_reg = ssel_reg
			self._ssel_risingedge = ssel_risingedge
			self._ssel_fallingedge = ssel_fallingedge
			
			self._sclk_reg = sclk_reg
			self._sclk_risingedge = sclk_risingedge
			self._sclk_fallingedge = sclk_fallingedge
			
			self._tx_buffer = tx_buffer
			self._rx_buffer = rx_buffer
		
		return m
	
	def ports(self):
		ports = [
			self.data_out, self.data_in,
			self.spi_sclk, self.spi_ssel, self.spi_mosi, self.spi_miso
		]
		
		if self._simulation:
			ports += [
				self._ssel_reg, self._ssel_risingedge, self._ssel_fallingedge,
				self._sclk_reg, self._sclk_risingedge, self._sclk_fallingedge,
				self._tx_buffer, self._rx_buffer
			]
		
		return ports
		
if __name__ == "__main__":
	m = SpiSlave(simulation=True)
	sim = Simulator(m)
	sim.add_clock(1e-8)
	
	def process():
		# Initial state
		yield m.spi_sclk.eq(1) # Clock starts high
		yield m.spi_ssel.eq(1) # Not selected
		yield m.spi_miso.eq(0) # Input data is low
		yield Delay(1e-6) # 1 uS delay
		
		for test_data in [0b11110000, 0b10101010, 0b00001111]:
			# Simulate start of transaction
			yield m.spi_ssel.eq(0) # Selected
			yield Delay(1e-6) # 1 uS delay
			
			# Simulate transaction
			for bit in range(8):
				yield m.spi_sclk.eq(0) # Falling edge of SPI clock
				yield m.spi_mosi.eq((test_data>>(7-bit))&1)
				yield Delay(1e-6) # 1 uS delay
				yield m.spi_sclk.eq(1) # Rising edge of SPI clock
				yield Delay(1e-6) # 1 uS delay
			
			# Simulate end of transaction
			yield m.spi_ssel.eq(1) # Not selected
			yield Delay(1e-6) # 1 uS delay
	
	sim.add_process(process)
	with sim.write_vcd("spi.vcd", "spi.gtkw", traces=m.ports()):
		sim.run()
