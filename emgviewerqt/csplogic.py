import numpy as np
import itertools as it
import collections

class CSPLogic(object):

    def createTimeStepsArray(self, signal):
            dt = float(signal.sampling_period)
            return np.linspace(0.0, float(dt*signal.size - dt), num=signal.size)

    def __init__(self, emg_signal):
        self.emg_signal = emg_signal
        self.timesteps = self.createTimeStepsArray(emg_signal)
        self.emg_signal_deriv = None
        self.CSPTuple = collections.namedtuple('CSPTuple', 'cspStartTime cspStartValue cspEndTime cspEndValue')
        self.trigger_dict = dict()
        self.fillTriggerDict()

    def fillTriggerDict(self):
        """
        Find the triggers using the first derivative of the EMG signal.
        For each epoch after a signal, look for samples where there has been
        no reading above a certain threshold in 6ms.  The longest interval of
        these samples is the cSP.
        http://stackoverflow.com/questions/1066758/find-length-of-sequences-of-identical-values-in-a-numpy-array
        http://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.strides.html
        """
        self.emg_signal_deriv = np.diff(self.emg_signal)
        for index in self.findTriggerIndices()[0]:
            self.trigger_dict[self.timesteps[index]] = self.findCSPWindow(index)


    def findTriggerIndices(self):
        """ Return a array of indices where a trigger has been detected.
        """
        trigger_mask = np.ma.masked_less(self.emg_signal_deriv, 1.0)
        return np.array(np.ma.nonzero(trigger_mask)) 

    def findCSPWindow(self, index):
        triggerTuple = self.CSPTuple(cspStartTime=self.timesteps[index+10], \
                                     cspStartValue=0.0, \
                                     cspEndTime = self.timesteps[index+30], \
                                     cspEndValue=0.0)
        return triggerTuple