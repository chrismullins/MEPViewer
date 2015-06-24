import numpy as np
import itertools as it


class ECGLogic(object):

    def createTimeStepsArray(self, signal):
        dt = float(signal.sampling_period)
        return np.linspace(0.0, float(dt*signal.size - dt), num=signal.size)

    def createSignalDeriv(self, signal):
        #deriv = np.diff(signal)
        return np.diff(signal)

    def __init__(self, emg_signal, window_begin=0.02, window_end=0.10):
        self.emg_signal = emg_signal
        self.timesteps = self.createTimeStepsArray(emg_signal)
        self.response_window_time = np.array([window_begin,window_end])
        self.response_window_indices = self.response_window_time*emg_signal.sampling_rate
        self.emg_signal_deriv = None
        self.trigger_indices = []
        self.trigger_index_minmax_dict = dict()
        self.trigger_time_minmax_dict = dict()

    def reportTriggersAndResponses(self):
        """Return a dict of [trigger_coord: [min_coord,max_coord]]
        """
        self.emg_signal_deriv = self.createSignalDeriv(self.emg_signal)
        self.findTriggers()
        for trigger_index in self.trigger_indices[0]:
            self.trigger_time_minmax_dict[ \
              self.timesteps[trigger_index]] = self.findResponseMinMaxs(trigger_index)
        return self.trigger_time_minmax_dict

    def findTriggers(self):
        # Trigger waiting period: for paired pulse data there are two triggers within 30ms of eachother.
        # Skip ahead the corresponding number of samples to avoid tagging both triggers. Non-pp data
        # doesn't have close-together triggers so we can do this safely for both.
        trigger_waiting_period = int(0.030*self.emg_signal.sampling_rate)
        # TODO: put in the PP hack again 
        trigger_mask = np.ma.masked_less(self.emg_signal_deriv, 1.0)
        print np.ma.nonzero(trigger_mask)
        self.trigger_indices = np.array(np.ma.nonzero(trigger_mask))
        return


    def findResponseMinMaxs(self, trigger_index):
        """Find the min and max response after a trigger
        at the given index"""
        window_start_index = trigger_index + int(self.response_window_indices[0])
        window_stop_index = trigger_index + int(self.response_window_indices[1])
        window = self.emg_signal[window_start_index:window_stop_index]
        max_index = np.argmax(window)
        min_index = np.argmin(window)
        window_max = window[max_index]
        window_min = window[min_index]
        final_min_index = window_start_index+min_index
        final_max_index = window_start_index+max_index
        return [ \
          np.array([self.timesteps[final_min_index],self.emg_signal[final_min_index]]), \
          np.array([self.timesteps[final_max_index],self.emg_signal[final_max_index]]) \
          ]