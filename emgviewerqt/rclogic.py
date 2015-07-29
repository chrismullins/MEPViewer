import numpy as np
import itertools as it
import collections



class RCLogic(object):

    def createTimeStepsArray(self, signal):
        dt = float(signal.sampling_period)
        return np.linspace(0.0, float(dt*signal.size - dt), num=signal.size)

    def readIntensityFromHeader(self, filename):
        import binascii
        CHUNKSIZE = 4
        file = open(filename, "rb")
        number_string = ''
        try:
            bytes_read = file.read(CHUNKSIZE)
            recording = False
            
            num_stims = 0
            while bytes_read:
                hexout = binascii.hexlify(bytes_read)
                ascout = binascii.unhexlify(hexout)
                if recording:
                    if hexout == '00000000':
                        recording = False
                        if num_stims == 3:
                            break
                    else:
                        number_string = ''.join((number_string, ascout))
                if 'Sti' in ascout:
                    recording = True
                    num_stims +=1
                bytes_read = file.read(CHUNKSIZE)
        finally:
            file.close()
        import re
        trimmed = re.sub(r"m:","", number_string)
        tmp_list = trimmed.rstrip().lstrip().split()
        number_list = [item.replace('\x00','') for item in tmp_list]
        return [int(item) for item in number_list]

    def __init__(self, emg_signal, fid=None, trigger_threshold=1.0, window_begin=0.02, window_end=0.10):
        self.emg_signal = emg_signal
        self.filename = fid.name
        self.emg_signal_deriv = np.diff(self.emg_signal)
        self.trigger_threshold = trigger_threshold
        self.timesteps = self.createTimeStepsArray(emg_signal)
        self.stim_order = self.readIntensityFromHeader(self.filename)
        self.MinMaxTuple = collections.namedtuple('MinMaxTuple', 'minTime minValue maxTime maxValue intensity peak2peak')
        ## Signal parameters:
        self.sig_x0 = None
        self.sig_y0 = None
        self.sig_c = None
        self.sig_k = None
        if fid:
            self.updateParameters(window_begin, window_end, trigger_threshold, filename=fid)

    def updateParameters(self, begin, end, threshold, filename):
        self.trigger_dict = dict()
        self.window_begin = begin
        self.window_end = end
        self.trigger_threshold = threshold
        self.fid = filename
        self.response_window_time = np.array([self.window_begin,self.window_end])
        self.response_window_indices = self.response_window_time*self.emg_signal.sampling_rate
        self.fillTriggerDict()

    def fillTriggerDict(self):
        """ Fill self.trigger_dict by detecting TMS spikes, and map those timepoints 
        to their min and max response values.
        """
        trigger_indices = self.findTriggerIndices(self.emg_signal_deriv, self.trigger_threshold)
        for i, index in enumerate(trigger_indices):
            self.trigger_dict[self.timesteps[index]] = self.findResponseMinMaxs(index, self.stim_order[i])

    
    def findTriggerIndices(self, signal_deriv, threshold):
        """Given a signal, return the indices which are less than a certain
        threshold.
        """
        trigger_array, = np.ma.nonzero(np.ma.masked_less(signal_deriv, threshold))
        trigger_list = trigger_array.tolist()
        # Trigger waiting period: for paired pulse data there are two triggers within 30ms of eachother.
        # Skip ahead the corresponding number of samples to avoid tagging both triggers. Non-pp data
        # doesn't have close-together triggers so we can do this safely for both.
        trigger_waiting_period = int(0.03*self.emg_signal.sampling_rate)
        # Quick way to find which triggers are close together
        secondary_triggers_indices, = np.where(abs(np.diff(trigger_list)) < trigger_waiting_period)
        # Delete-by-index must be done in reverse order.  Otherwise all the indices shift
        for sec_trigger in sorted(secondary_triggers_indices, reverse=True):
            del trigger_list[sec_trigger+1]
        return trigger_list

    def findResponseMinMaxs(self, trigger_index, intensity):
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
                                   intensity=intensity, \
                                   peak2peak=peak2peak)
        return triggerTuple

    def getMeanMEPReadings(self):
        intensities = sorted(list(set(self.stim_order)))
        mep_dict = collections.defaultdict(list)
        # dict mapping intensities to a list of MEPs at that intensity
        for ttime, mmtup in self.trigger_dict.iteritems():
            mep_dict[mmtup.intensity].append(mmtup.peak2peak)
        means = np.array([np.mean(mep_dict[i]) for i in intensities])
        stddev = np.array([np.std(mep_dict[i]) for i in intensities])
        return np.array(intensities), means, stddev

    def getSigmoidFit(self):
        """ Return two vectors specifying x and y for the best sigmoid fit of the 
        mean MEP readings. The residual is defined as the difference between each data point 
        and its corresponding point on a sigmoid fitted to the best current guess of parameters.
        http://www.tau.ac.il/~kineret/amit/scipy_tutorial/

        The sigmoid function is defined as c / (1 + e^(-k(x-x0))) + y0 where c is the max value of the 
        curve, x0 is the x value of the sigmoid midpoint, and k is the steepness of the curve.
        """
        import scipy.optimize
        def sigmoid(p,x):
            x0,y0,c,k=p
            y = c / (1 + np.exp(-k*(x-x0))) + y0
            return y

        def residuals(p,x,y):
            return y - sigmoid(p,x)

        x, y, stddev = self.getMeanMEPReadings()

        p_guess=(np.median(x),np.median(y),1.0,1.0)
        p, cov, infodict, mesg, ier = scipy.optimize.leastsq(
            residuals,p_guess,args=(x,y),full_output=1)  
        x0,y0,c,k=p
        self.sig_x0 = x0
        self.sig_y0 = y0
        self.sig_c = c
        self.sig_k = k


        xp = np.linspace(np.array(self.stim_order).min(), np.array(self.stim_order).max(), 1500)
        pxp=sigmoid(p,xp)
        return xp, pxp

    def writeInfoToCSV(self, outputPath):
        intensities = sorted(list(set(self.stim_order)))
        mep_dict = collections.defaultdict(list)
        # dict mapping intensities to a list of MEPs at that intensity
        for ttime, mmtup in self.trigger_dict.iteritems():
            mep_dict[mmtup.intensity].append(mmtup.peak2peak)
        footerList = []
        for intensity, p2plist in mep_dict.iteritems():
            p2ps = "\n".join(str(p2p) for p2p in p2plist)
            average = str(np.mean(np.array(p2plist)))
            average_str = "Average: {}".format(average)
            intro = "Intensity: {}".format(intensity)
            footerList.append("\n".join((intro, p2ps, average_str)))
        #rcInfo = self.getRCInfo()

        np.savetxt(outputPath, \
            np.vstack([
            np.hstack(arr.reshape(-1,1) for arr in \
                [self.getTriggerTimePoints(), \
                 self.getTriggerMinTimes(), \
                 self.getTriggerMins(), \
                 self.getTriggerMaxTimes(), \
                 self.getTriggerMaxs(), \
                 self.getTriggerMeans(), \
                 self.getIntensities(), \
                 self.getTriggerP2Ps()])]), \
            header="trigger,min_time,min_value,max_time,max_value,mean,intensity,peak2peak", delimiter=",", \
            footer="\n".join(footerList), \
            fmt="%.5e")

    def getRCInfo(self):
        """
        From http://jn.physiology.org/content/94/4/2844.short:

        At a given stimulation intensity, the four peak-to-peak MEPs were measured 
        and then averaged together. The averaged MEP response was plotted against 
        the corresponding stimulation intensity as per Capaday et al. (1999) to produce 
        a recruitment curve (Fig. 1B). A four-parameter sigmoid function (Boltzman) was 
        fit to this recruitment curve (see also Knash et al. 2003) that included a 
        parameter for background EMG activity given that there was a measurable peak-to-peak 
        EMG response when no MEP was present. Four specific parameters of the recruitment 
        and sigmoid curves were measured: MEPmax[r], which was the largest MEP evoked in the 
        facilitated muscle and typically occurred at the largest stimulation intensities; 
        MEPh, which was measured from the sigmoid curve at the stimulation intensity that 
        produced a half-maximum response in the before-training condition (Carroll et al. 2001; Knash et al. 2003); 
        [STOP that sentence makes no sense. Later in the paper, they state: "MEPh was measured as 
        the mid-point of the minimum and maximum value of the sigmoid curve". Let's go with that.]
        MEPthresh, which was the stimulation intensity that produces 5% of maximum of the 
        sigmoid curve (similar to Carroll et al. 2001); and the slope of the steepest region 
        of the sigmoid curve (measured near MEPh) (Devanne et al. 1997). In addition to 
        measuring the peak-to-peak values of the MEP, the mean rectified value of EMG over 
        the period of measurement of the MEP was also calculated. To calculate the average 
        background EMG activity at each stimulation intensity, the mean amplitude of the 
        rectified EMG was calculated over a 27-ms window prior to the stimulation with the 
        mean of all points for a given recruitment curve marked by a horizontal line (see Fig. 1B, bottom).
        """
        print("*"*80)
        print("Info for: {}".format(self.filename))
        maxMEP = 0
        maxMEPIntensity = 0
        intensities = sorted(list(set(self.stim_order)))
        mep_dict = collections.defaultdict(list)
        # dict mapping intensities to a list of MEPs at that intensity
        for ttime, mmtup in self.trigger_dict.iteritems():
            mep_dict[mmtup.intensity].append(mmtup.peak2peak)
        for intensity, meplist in mep_dict.iteritems():
            max_mep = max(meplist)
            if max_mep > maxMEP:
                maxMEPIntensity, maxMEP = intensity, max_mep
        print("Maximum evoked MEP was {} at intensity {}.".format(maxMEP, maxMEPIntensity))

        # midMEP is the midpoint of the minimum and maximum control points of the recruitment
        # curve.
        intensity_arr, means_arr, stddev_arr = self.getMeanMEPReadings()
        MEP_h = np.mean([np.min(means_arr),np.max(means_arr)])
        # Now we have the midpoint MEP_h, but what intensity would we expect to elicit that response,
        # according to the sigmoid?
        sig_mo, sig_y = self.getSigmoidFit()
        MEP_h_MO = sig_mo[np.argmin(abs(sig_y-MEP_h))]
        print("Midpoint (MEP_h) was {} at machine output {}".format(MEP_h, MEP_h_MO))

        # Maximum slope is also important
        d_sig_y = np.diff(sig_y)
        max_slope = np.max(d_sig_y) / np.diff(sig_mo)[np.argmax(d_sig_y)]
        max_slope_mo = sig_mo[np.argmax(d_sig_y)]
        print("Max slope was {} /s at machine output {}".format(max_slope, max_slope_mo))

        # Lastly we need MEP_thresh, the intensity which elicited an MEP of 5% of the maximum
        # control point.  Since this isn't a MEP, I'm going to call it MO_thresh (machine output threshold)
        max_sigmoid = np.max(means_arr)
        MEP_thresh = 0.05*max_sigmoid
        MO_thresh_index = np.argmin(abs(sig_y-MEP_thresh))
        #MO_thresh = sig_y[MO_thresh_index]
        MO_thresh = sig_mo[MO_thresh_index]
        print("5% of the maximum intensity ({} mV) was reached at machine output {} ".format(MEP_thresh, MO_thresh))

        # Also let's print the equation parameters:
        print('''\
        x0 = {x0}
        y0 = {y0}
        c = {c}
        k = {k}
        '''.format(x0=self.sig_x0,y0=self.sig_y0,c=self.sig_c,k=self.sig_k))


        

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

    def getIntensities(self):
        return np.array([self.trigger_dict[trigger_time].intensity for trigger_time in sorted(self.trigger_dict)])