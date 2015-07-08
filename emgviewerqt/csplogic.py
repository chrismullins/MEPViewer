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
        trigger_indices = self.findTriggerIndices()[0]
        for i, trig_index in enumerate(trigger_indices):
            #print i, index
            if i <= trigger_indices.size-2:
                next_trig_index = trigger_indices[i+1]
            elif i == trigger_indices.size-1:
                next_trig_index = self.emg_signal.size-1
            print trig_index, next_trig_index
            self.trigger_dict[self.timesteps[trig_index]] = self.findCSPWindow(trig_index, next_trig_index)


    def findTriggerIndices(self):
        """ Return a array of indices where a trigger has been detected.
        """
        trigger_mask = np.ma.masked_less(self.emg_signal_deriv, 3.0)
        return np.array(np.ma.nonzero(trigger_mask)) 

    def findCSPWindow(self, index, next_index):
        # triggerTuple = self.CSPTuple(cspStartTime=self.timesteps[index+10], \
        #                              cspStartValue=0.0, \
        #                              cspEndTime = self.timesteps[index+30], \
        #                              cspEndValue=0.0)
        # print self.emg_signal[index], self.emg_signal[next_index]
        # return triggerTuple
        signal_window = self.emg_signal[index:next_index]
        #window_mask = np.ma.masked_less(signal_window, 0.01)
        window_mask = np.zeros(signal_window.size)
        # We choose 0.1 mV as the threshold right now
        window_mask[signal_window < 0.1] = 1.0
        bounded_mask = np.hstack(([0], window_mask, [0]))
        difs = np.diff(bounded_mask)
        run_starts, = np.where(difs > 0)
        run_ends, = np.where(difs < 0)
        run_lengths = run_ends - run_starts
        longest_run_index = np.argmax(run_lengths)
        absolute_start_index = index+run_starts[longest_run_index]
        absolute_end_index = index+run_ends[longest_run_index]
        triggerTuple = self.CSPTuple(cspStartTime=self.timesteps[absolute_start_index], \
                                     cspStartValue=self.emg_signal[absolute_start_index], \
                                     cspEndTime=self.timesteps[absolute_end_index], \
                                     cspEndValue=self.emg_signal[absolute_end_index])
        return triggerTuple


