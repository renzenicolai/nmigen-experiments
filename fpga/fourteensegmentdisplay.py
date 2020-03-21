from nmigen import *
from nmigen.build import Platform, ResourceError
from nmigen.back.pysim import Simulator, Delay, Settle

# Small helper classes to simulate the structure of the platform device

class _OutputSimulator():
	def __init__(self, signal):
		self.signal = signal
		self.eq = self.signal.eq
class _SegmentSimulator():
	def __init__(self, signal):
		self.o = _OutputSimulator(signal)

class FourteenSegmentDisplay(Elaboratable):
	"""
		This submodule shows the provided ASCII character on a 14 segment display.
		The eight bit of the input data is used to switch the dot on or off.
	"""
	def __init__(self, deviceType="alnum_led", deviceId=0, simulation=False):
		# Public
		self.data        = Signal(8, reset=0)
		
		self.simulation  = simulation
		self.simSignals  = []
		
		# Private
		self._device     = None
		self._deviceType = deviceType
		self._deviceId   = deviceId
		self._segments   = ['a','b','c','d','e','f','g','h','j','k','l','m','n','p']
		self._dotSegment = 'dp'
		self._lut        = [
			[0,0,0,0,0,0, 0,0,0, 0, 0,0,0, 0], #   (0x20)
			[0,0,0,0,1,1, 0,0,0, 0, 0,0,0, 0], # ! (0x21)
			[0,1,0,0,0,1, 0,0,0, 0, 0,0,0, 0], # " (0x22)
			[0,1,1,1,0,0, 0,1,0, 1, 0,1,0, 1], # # (0x23)
			[1,0,1,1,0,1, 0,1,0, 1, 0,1,0, 1], # $ (0x24)
			[0,0,1,0,0,1, 0,0,1, 0, 0,0,1, 0], # % (0x25)
			[1,0,0,1,1,0, 1,0,1, 0, 1,0,0, 1], # & (0x26)
			[0,1,0,0,0,0, 0,1,0, 0, 0,0,0, 0], # ' (0x27)
			[1,0,0,1,1,1, 0,0,0, 0, 0,0,0, 0], # ( (0x28)
			[1,1,1,1,0,0, 0,0,0, 0, 0,0,0, 0], # ) (0x29)
			[0,0,0,0,0,0, 1,1,1, 1, 1,1,1, 1], # * (0x2A)
			[0,0,0,0,0,0, 0,1,0, 1, 0,1,0, 1], # + (0x2B)
			[0,0,0,0,0,0, 0,0,0, 0, 1,0,0, 0], # , (0x2C)
			[0,0,0,0,0,0, 0,0,0, 1, 0,0,0, 1], # - (0x2D)
			[0,0,0,0,0,0, 0,0,0, 0, 0,1,0, 0], # . (0x2E)
			[0,0,0,0,0,0, 0,0,1, 0, 0,0,1, 0], # / (0x2F)
			[1,1,1,1,1,1, 0,0,0, 0, 0,0,0, 0], # 0 (0x30)
			[0,1,1,0,0,0, 0,0,1, 0, 0,0,0, 0], # 1 (0x31)
			[1,1,0,1,1,0, 0,0,0, 1, 0,0,0, 1], # 2 (0x32)
			[1,1,1,1,0,0, 0,0,0, 1, 0,0,0, 0], # 3 (0x33)
			[0,1,1,0,0,1, 0,0,0, 1, 0,0,0, 1], # 4 (0x34)
			[1,0,1,1,0,1, 0,0,0, 1, 0,0,0, 1], # 5 (0x35)
			[1,0,1,1,1,1, 0,0,0, 1, 0,0,0, 1], # 6 (0x36)
			[1,0,0,0,0,0, 0,0,1, 0, 0,1,0, 0], # 7 (0x37)
			[1,1,1,1,1,1, 0,0,0, 1, 0,0,0, 1], # 8 (0x38)
			[1,1,1,0,0,1, 0,0,0, 1, 0,0,0, 1], # 9 (0x39)
			[0,0,0,0,0,0, 0,1,0, 0, 0,1,0, 0], # : (0x3A)
			[0,0,0,0,0,0, 0,1,0, 0, 0,0,1, 0], # ; (0x3B)
			[0,0,0,0,0,0, 0,0,1, 0, 1,0,0, 0], # < (0x3C)
			[0,0,0,1,0,0, 0,0,0, 1, 0,0,0, 1], # = (0x3D)
			[0,0,0,0,0,0, 1,0,0, 0, 0,0,1, 0], # > (0x3E)
			[1,0,0,0,0,1, 0,0,1, 0, 0,1,0, 0], # ? (0x3F)
			[1,1,1,1,1,1, 1,0,1, 0, 1,0,1, 0], # @ (0x40)
			[1,1,1,0,1,1, 0,0,0, 1, 0,0,0, 1], # A (0x41)
			[1,1,1,1,0,0, 0,1,0, 1, 0,1,0, 0], # B (0x42)
			[1,0,0,1,1,1, 0,0,0, 0, 0,0,0, 0], # C (0x43)
			[1,1,1,1,0,0, 0,1,0, 0, 0,1,0, 0], # D (0x44)
			[1,0,0,1,1,1, 0,0,0, 1, 0,0,0, 1], # E (0x45)
			[1,0,0,0,1,1, 0,0,0, 1, 0,0,0, 1], # F (0x46)
			[1,0,1,1,1,1, 0,0,0, 1, 0,0,0, 0], # G (0x47)
			[0,1,1,0,1,1, 0,0,0, 1, 0,0,0, 1], # H (0x48)
			[1,0,0,1,0,0, 0,1,0, 0, 0,1,0, 0], # I (0x49)
			[0,1,1,1,1,0, 0,0,0, 0, 0,0,0, 0], # J (0x4A)
			[0,0,0,0,1,1, 0,0,1, 0, 1,0,0, 1], # K (0x4B)
			[0,0,0,1,1,1, 0,0,0, 0, 0,0,0, 0], # L (0x4C)
			[0,1,1,0,1,1, 1,0,1, 0, 0,0,0, 0], # M (0x4D)
			[0,1,1,0,1,1, 1,0,0, 0, 1,0,0, 0], # N (0x4E)
			[1,1,1,1,1,1, 0,0,0, 0, 0,0,0, 0], # O (0x4F)
			[1,1,0,0,1,1, 0,0,0, 1, 0,0,0, 1], # P (0x50)
			[1,1,1,1,1,1, 0,0,0, 0, 1,0,0, 0], # Q (0x51)
			[1,1,0,0,1,1, 0,0,0, 1, 1,0,0, 1], # R (0x52)
			[1,0,1,1,0,0, 1,0,0, 1, 0,0,0, 0], # S (0x53)
			[1,0,0,0,0,0, 0,1,0, 0, 0,1,0, 0], # T (0x54)
			[0,1,1,1,1,1, 0,0,0, 0, 0,0,0, 0], # U (0x55)
			[0,0,0,0,1,1, 0,0,1, 0, 0,0,1, 0], # V (0x56)
			[0,1,1,0,1,1, 0,0,0, 0, 1,0,1, 0], # W (0x57)
			[0,0,0,0,0,0, 1,0,1, 0, 1,0,1, 0], # X (0x58)
			[0,0,0,0,0,0, 1,0,1, 0, 0,1,0, 0], # Y (0x59)
			[1,0,0,1,0,0, 0,0,1, 0, 0,0,1, 0], # Z (0x5A)
			[1,0,0,1,1,1, 0,0,0, 0, 0,0,0, 0], # [ (0x5B)
			[0,0,0,0,0,0, 1,0,0, 0, 1,0,0, 0], # \ (0x5C)
			[1,1,1,1,0,0, 0,0,0, 0, 0,0,0, 0], # ] (0x5D)
			[1,1,0,0,0,1, 0,0,0, 0, 0,0,0, 0], # ^ (0x5E)
			[0,0,0,1,0,0, 0,0,0, 0, 0,0,0, 0], # _ (0x5F)
			[0,0,0,0,0,0, 1,0,0, 0, 0,0,0, 0], # ` (0x60)
			[1,1,1,1,1,0, 0,0,0, 1, 0,0,0, 1], # a (0x61)
			[0,0,0,1,1,1, 0,0,0, 0, 1,0,0, 1], # b (0x62)
			[0,0,0,1,1,0, 0,0,0, 1, 0,0,0, 1], # c (0x63)
			[0,1,1,1,0,0, 0,0,0, 1, 0,0,1, 0], # d (0x64)
			[1,0,0,1,1,1, 0,0,0, 0, 0,0,0, 1], # e (0x65)
			[1,0,0,0,1,1, 0,0,0, 0, 0,0,0, 1], # f (0x66)
			[1,1,1,1,0,0, 1,0,0, 1, 0,0,0, 0], # g (0x67)
			[0,0,1,0,1,1, 0,0,0, 1, 0,0,0, 1], # h (0x68)
			[0,0,0,0,0,0, 0,0,0, 0, 0,1,0, 0], # i (0x69)
			[0,1,1,1,0,0, 0,0,0, 0, 0,0,0, 0], # j (0x6A)
			[0,0,0,0,1,1, 0,0,1, 0, 1,0,0, 0], # k (0x6B)
			[0,0,0,0,0,0, 0,1,0, 0, 0,1,0, 0], # l (0x6C)
			[0,0,1,0,1,0, 0,0,0, 1, 0,1,0, 1], # m (0x6D)
			[0,0,0,0,1,0, 0,0,0, 0, 1,0,0, 1], # n (0x6E)
			[0,0,1,1,1,0, 0,0,0, 1, 0,0,0, 1], # o (0x6F)
			[1,0,0,0,1,1, 0,0,1, 0, 0,0,0, 1], # p (0x70)
			[1,1,0,0,0,1, 0,0,0, 1, 1,0,0, 1], # q (0x71)
			[0,0,0,0,1,0, 0,0,0, 0, 0,0,0, 1], # r (0x72)
			[1,0,1,1,0,0, 1,0,0, 1, 0,0,0, 0], # s (0x73)
			[0,0,0,1,1,1, 0,0,0, 0, 0,0,0, 1], # t (0x74)
			[0,0,1,1,1,0, 0,0,0, 0, 0,0,0, 0], # u (0x75)
			[0,0,0,0,1,0, 0,0,0, 0, 0,0,1, 0], # v (0x76)
			[0,0,1,0,1,0, 0,0,0, 0, 1,0,1, 0], # w (0x77)
			[0,0,0,0,0,0, 1,0,1, 0, 1,0,1, 0], # x (0x78)
			[0,1,1,1,0,0, 0,1,0, 1, 0,0,0, 0], # y (0x79)
			[1,0,0,1,0,0, 0,0,1, 0, 0,0,1, 0], # z (0x7A)
			[1,0,0,1,0,0, 1,0,0, 0, 0,0,1, 1], # { (0x7B)
			[0,0,0,0,0,0, 0,1,0, 0, 0,1,0, 0], # | (0x7C)
			[1,0,0,1,0,0, 0,0,1, 1, 1,0,0, 0], # } (0x7D)
			[0,0,0,0,0,0, 0,0,0, 1, 0,0,0, 1], # ~ (0x7E)
		]
	
	def elaborate(self, platform: Platform) -> Module:
		m = Module()
		if self.simulation:
			self._device = {}
			for segment in self._segments + [self._dotSegment]:
				s = Signal(1)
				s.name = segment
				self.simSignals.append(s)
				self._device[segment] = _SegmentSimulator(s)
		else:
			self._device = platform.request(self._deviceType, self._deviceId)
		
		# Remove the eighth bit from the data signal and map the seven remaining bits onto the LUT
		data7 = Signal(unsigned(7))
		with m.If(self.data[0:7] < 0x20): # Out of range
			m.d.comb += data7.eq(0) # Set to SPACE (0x20), 0 in our LUT, when data is out of range
		with m.Else():
			m.d.comb += data7.eq(self.data[0:7]-0x20)
		
		# Drive the dot segment using the eighth bit of the data signal
		m.d.comb += self._device[self._dotSegment].o.eq(self.data[7])
		
		# Drive the other fourteen segments using the LUT
		with m.Switch(data7):
			for i in range(len(self._lut)):
				with m.Case(i): # (SPACE to ~)
					for j in range(len(self._segments)):
						m.d.comb += self._device[self._segments[j]].o.eq(self._lut[i][j])
			with m.Default(): # (0x7F / DEL)
				for j in range(len(self._segments)):
						m.d.comb += self._device[self._segments[j]].o.eq(1)
		return m
	
	def ports(self):
		ports = [self.data]
		if self.simulation:
			ports.extend(self.simSignals)
		return ports
		
if __name__ == "__main__":
	m = FourteenSegmentDisplay(simulation = True)
	sim = Simulator(m)
	
	def process():
		# This design consist purely of combinational logic
		# so we just loop through all possible input values
		for i in range(256):
			yield m.data.eq(i)
			yield Delay(1e-6)
			yield Settle()
	
	sim.add_process(process)
	with sim.write_vcd("test.vcd", "test.gtkw", traces=m.ports()):
		sim.run()
