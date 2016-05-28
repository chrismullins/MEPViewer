import numpy as np
import itertools as it
import collections


class EMGLogic(object):

    def createTimeStepsArray(self, signal):
        dt = float(signal.sampling_period)
        return np.linspace(0.0, float(dt*signal.size - dt), num=signal.size)

    def __init__(self, emg_signal, fid=None, trigger_threshold=1.0, window_begin=0.02, window_end=0.10, \
     paired_pulse=True, pp_interval=0.03):
        self.emg_signal = emg_signal
        self.filename = fid.name
        # Use np.array() to avoid the "<ufunc 'less'> not supported by quantities" error
        self.emg_signal_deriv = np.array(np.diff(self.emg_signal))
        self.trigger_threshold = trigger_threshold
        self.paired_pulse = paired_pulse
        self.pp_interval = pp_interval
        self.timesteps = self.createTimeStepsArray(emg_signal)
        self.MinMaxTuple = collections.namedtuple('MinMaxTuple', 'minTime minValue maxTime maxValue peak2peak')
        self.updateParameters(window_begin, window_end, trigger_threshold)

    def updateParameters(self, begin, end, trigger_threshold, fill_trigger_dict=False):
        self.trigger_dict = dict()
        self.window_begin = begin
        self.window_end = end
        self.trigger_threshold = trigger_threshold
        self.response_window_time = np.array([self.window_begin,self.window_end])
        self.response_window_indices = self.response_window_time*self.emg_signal.sampling_rate
        if fill_trigger_dict:
            self.fillTriggerDict()

    def fillTriggerDict(self):
        """ Fill self.trigger_dict by detecting TMS spikes, and map those timepoints 
        to their min and max response values.
        """
        trigger_indices = self.findTriggerIndices(self.emg_signal_deriv, self.trigger_threshold)
        for index in trigger_indices:
            self.trigger_dict[self.timesteps[index]] = self.findResponseMinMaxs(index)

    def findTriggerIndices(self, signal_deriv, threshold):
        """Given a signal, return the indices which are less than a certain
        threshold.
        """
        trigger_array, = np.ma.nonzero(np.ma.masked_less(signal_deriv, threshold))
        trigger_list = trigger_array.tolist()
        # Trigger waiting period: for paired pulse data there are two triggers within 30ms of eachother.
        # Skip ahead the corresponding number of samples to avoid tagging both triggers. Non-pp data
        # doesn't have close-together triggers so we can do this safely for both.
        if self.paired_pulse:
            trigger_waiting_period = int(self.pp_interval*self.emg_signal.sampling_rate)
            # Quick way to find which triggers are close together
            secondary_triggers_indices, = np.where(abs(np.diff(trigger_list)) < trigger_waiting_period)
            # Delete-by-index must be done in reverse order.  Otherwise all the indices shift
            for sec_trigger in sorted(secondary_triggers_indices, reverse=True):
                del trigger_list[sec_trigger+1]
        return trigger_list

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
        # Prepare return values
        minTime=self.timesteps[final_min_index]
        minValue=self.emg_signal[final_min_index]
        maxTime=self.timesteps[final_max_index]
        maxValue=self.emg_signal[final_max_index]
        peak2peak = abs(maxValue) + abs(minValue)
        triggerTuple = self.MinMaxTuple(minTime=minTime, \
                                   minValue=minValue, \
                                   maxTime=maxTime, \
                                   maxValue=maxValue, \
                                   peak2peak=peak2peak)
        return triggerTuple

    def addTriggerTimepoint(self, trigger_time):
        new_trigger_index = np.argmin(abs(self.timesteps - trigger_time))
        trigger_tuple = self.findResponseMinMaxs(new_trigger_index)
        self.trigger_dict[self.timesteps[new_trigger_index]] = trigger_tuple
        #return self.timesteps[new_trigger_index]
        return trigger_tuple


    def writeInfoToCSV(self, outputPath):
        np.savetxt(outputPath, \
            np.vstack([
            np.hstack(arr.reshape(-1,1) for arr in \
                [self.getTriggerTimePoints(), \
                 self.getTriggerMinTimes(), \
                 self.getTriggerMins(), \
                 self.getTriggerMaxTimes(), \
                 self.getTriggerMaxs(), \
                 self.getTriggerMeans(), \
                 self.getTriggerP2Ps()]),
                  \
                np.array([0,0,0,0,0,0,self.getFinalAverage()])]), \
            header="trigger,min_time,min_value,max_time,max_value,mean,peak2peak,finalAverage", delimiter=",", \
            fmt="%.5e")

    def getSignalInfo(self):
        infoStrings = []
        infoStrings.append("*"*80)
        infoStrings.append("Info for: {}".format(self.filename))
        infoStrings.append("[trigger time, MEP Amplitude]")
        infoStrings.append("=============================")
        infoStrings.append(str(np.hstack(arr.reshape(-1,1) for arr in [self.getTriggerTimePoints(), self.getTriggerP2Ps()])))
        infoStrings.append("Average MEP Amplitude: {}".format(self.getFinalAverage()))
        return "\n".join(infoStrings)

    def getTriggerTimePoints(self):
        return np.array(sorted(self.trigger_dict))

    def getTriggerMins(self):
        return np.array([self.trigger_dict[trigger_time].minValue for trigger_time in sorted(self.trigger_dict)])

    def getTriggerMinTimes(self):
        return np.array([self.trigger_dict[trigger_time].minTime for trigger_time in sorted(self.trigger_dict)])

    def getTriggerMaxs(self):
        return np.array([self.trigger_dict[trigger_time].maxValue for trigger_time in sorted(self.trigger_dict)])

    def getTriggerMaxTimes(self):
        return np.array([self.trigger_dict[trigger_time].maxTime for trigger_time in sorted(self.trigger_dict)])

    def getTriggerMeans(self):
        return (self.getTriggerMins() + self.getTriggerMaxs()) / 2

    def getTriggerP2Ps(self):
        return abs(self.getTriggerMins()) + abs(self.getTriggerMaxs())

    def getFinalAverage(self):
        return np.mean(self.getTriggerP2Ps())