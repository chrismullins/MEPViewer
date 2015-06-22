import neo as neo

class reader:

	def __init__(self, filename=None):
	    self.spikeReader = neo.io.Spike2IO(filename=filename)
	    self.seg = self.spikeReader.read_segment(lazy=False, cascade=True)

	#---------------------------------------------------------------------------
	def GetECGSignal(self):
		#r = neo.io.Spike2IO(filename=inputFile.name)
	    #seg = self.spikeReader.read_segment(lazy=False, cascade=True)
	    return self.seg.analogsignals[0]

	#---------------------------------------------------------------------------
	def GetSampleRate(self):
	    return self.seg.analogsignals[0].sampling_rate