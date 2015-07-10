import numpy as np
import itertools as it
import collections

class CSPLogic(object):

    def createTimeStepsArray(self, signal):
            dt = float(signal.sampling_period)
            return np.linspace(0.0, float(dt*signal.size - dt), num=signal.size)

    def __init__(self, emg_signal, trigger_threshold=1.0, window_begin=0.02, window_end=1.02, csp_threshold=0.1):
        self.emg_signal = emg_signal
        self.timesteps = self.createTimeStepsArray(emg_signal)
        self.emg_signal_deriv = np.diff(emg_signal)
        self.CSPTuple = collections.namedtuple('CSPTuple', 'cspStartTime cspStartValue cspEndTime cspEndValue')
        self.trigger_dict = dict()
        self.updateParameters(window_begin, window_end, trigger_threshold, csp_threshold)

    def updateParameters(self, begin, end, trigger_threshold, csp_threshold):
        self.csp_window_begin = begin
        self.csp_window_end = end
        self.trigger_threshold = trigger_threshold
        self.csp_threshold = csp_threshold
        self.response_window_time = np.array([self.csp_window_begin,self.csp_window_end])
        self.response_window_indices = self.response_window_time*self.emg_signal.sampling_rate
        self.fillTriggerDict()

    def fillTriggerDict(self):
        """
        Find the triggers using the first derivative of the EMG signal.
        For each epoch after a signal, look for samples where there has been
        no reading above a certain threshold in 6ms.  The longest interval of
        these samples is the cSP.
        """
        self.emg_signal_deriv = np.diff(self.emg_signal)
        trigger_indices = self.findTriggerIndices(self.emg_signal_deriv, self.trigger_threshold)
        for trigger_index in trigger_indices:
            self.trigger_dict[self.timesteps[trigger_index]] = self.findCSPWindow(signal=self.emg_signal, trigger_index=trigger_index)

    def findTriggerIndices(self, signal_deriv, threshold):
        """Given a signal, return the indices which are less than a certain
        threshold.
        """
        trigger_array, = np.ma.nonzero(np.ma.masked_less(signal_deriv, threshold))
        trigger_list = trigger_array.tolist()
        # Trigger waiting period: for paired pulse data there are two triggers within 30ms of eachother.
        # Skip ahead the corresponding number of samples to avoid tagging both triggers. Non-pp data
        # doesn't have close-together triggers so we can do this safely for both.
        trigger_waiting_period = int(0.30*self.emg_signal.sampling_rate)
        # Quick way to find which triggers are close together
        secondary_triggers_indices, = np.where(abs(np.diff(trigger_list)) < trigger_waiting_period)
        # Delete-by-index must be done in reverse order.  Otherwise all the indices shift
        for sec_trigger in sorted(secondary_triggers_indices, reverse=True):
            del trigger_list[sec_trigger+1]
        return trigger_list

    def findCSPWindow(self, signal, trigger_index):
        window_start_index = trigger_index + int(self.response_window_indices[0])
        window_stop_index = trigger_index + int(self.response_window_indices[1])
        signal_window = self.emg_signal[window_start_index:window_stop_index]
        window_mask = np.zeros(signal_window.size)
        # We choose 0.1 mV as the threshold right now
        window_mask[signal_window < self.csp_threshold] = 1.0
        bounded_mask = np.hstack(([0], window_mask, [0]))
        difs = np.diff(bounded_mask)
        # Runs of less than threshold will begin with 1 and
        # end with -1 in the bounded_mask array.
        run_starts, = np.where(difs > 0)
        run_ends, = np.where(difs < 0)
        run_lengths = run_ends - run_starts
        longest_run_index = np.argmax(run_lengths)
        absolute_start_index = trigger_index+run_starts[longest_run_index]
        absolute_end_index = trigger_index+run_ends[longest_run_index]
        triggerTuple = self.CSPTuple(cspStartTime=self.timesteps[absolute_start_index], \
                                     cspStartValue=self.emg_signal[absolute_start_index], \
                                     cspEndTime=self.timesteps[absolute_end_index], \
                                     cspEndValue=self.emg_signal[absolute_end_index])
        return triggerTuple


