# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 09:10:23 2020

@author: eric
"""

import experiment
import numpy as np
from scipy.signal import hilbert
# import matplotlib.pyplot as plt
# plt.rcParams['svg.fonttype'] = 'none'
from mne.time_frequency import psd_array_multitaper
from neo.io import NeuralynxIO
import misc_Functions

class NeuralynxEEG(experiment.experiment):
    """This is the class definition for handling Neuralynx EEG data."""
    def importEphysData(self, channels='all', importEvents=True):
        """Import Neuralynx continuously sampled channel data and associated events.
        CHANNELS can be 'all', 'none' (if you just want to import the events),
        or a string or list of strings."""
        self._recording = NeuralynxIO(self.experiment['directory'])
        self._ephysData = self._recording.read_block(signal_group_mode='split-all')
        self.samplingRate = {}
        self.tEEG = {}
        self.EEG = {}
        if channels == 'all':
            channels = self.experiment['LFP and EEG CSCs'].split(';')
        if channels != 'none':
            for k, c in enumerate(self._ephysData.segments[0].analogsignals):
                if c.name in channels:
                    self.samplingRate[c.name] = c.sampling_rate.magnitude
                    dt = 1/self.samplingRate[c.name]
                    tStart = c.t_start.magnitude
                    tStop = self._ephysData.segments[-1].analogsignals[k].t_stop.magnitude
                    # Since tStop is actually one timestep beyond the time of the last sample, 
                    # evaluate whether there needs to be another time point at the end
                    # to accommodate the timing of the last segment (and not leave the
                    # last element stranded). The '=' in the '<=' is to account for the
                    # fact that .argmin() in self._makeEEGarrays() looks for the first
                    # occurance of the minimum when there is more than one candidate.
                    if (tStop - tStart) % dt <= (dt / 2):
                        tStop -= 0.51 * dt # subtract just over half of a dt to bump it down a time point
                    self.tEEG[c.name] = np.arange(tStart, tStop, dt)
                    self._makeEEGarrays(k)
                    # For each channel, after making the EEG arrays, find the element
                    # of the time vector closest to self.experiment['zero time (s)']
                    # and subtract the time at that element from the entire time array
                    zeroIdx = (np.abs(self.tEEG[c.name] - self.experiment['zero time (s)'])).argmin()
                    self.tEEG[c.name] -= self.tEEG[c.name][zeroIdx]
        if importEvents:
            self.NeuralynxImportEvents(analogSignalImported=True)
    
    
    def _makeEEGarrays(self, chNum):
        """Method for concatenating EEG data and interpolating data between timestamp jumps.
        CHNUM is the channel number"""
        # Make a vector of NaNs equal in length to the time vector
        chName = self._ephysData.segments[0].analogsignals[chNum].name
        self.EEG[chName] = np.nan * np.ones(np.shape(self.tEEG[chName]))
        for seg in self._ephysData.segments:
            segSize = seg.analogsignals[chNum].size
            startIdx = (np.abs(self.tEEG[chName] - seg.t_start.magnitude)).argmin()
            # Interpolate the chunk between the last segment and the start of the current segment
            if seg.index > 0:
                interpStartIdx = np.where(np.isnan(self.EEG[chName]))[0][0]
                interpSegSize = startIdx-interpStartIdx
                self.EEG[chName][interpStartIdx:startIdx] = np.reshape(np.linspace(self.EEG[chName][interpStartIdx-1], seg.analogsignals[chNum][0].magnitude, interpSegSize+2)[1:-1], interpSegSize)
            # Add on the current segment
            self.EEG[chName][startIdx:(startIdx+segSize)] = np.reshape(seg.analogsignals[chNum].magnitude, segSize)


    def NeuralynxImportEvents(self, analogSignalImported=False):
        """Method for importing Neuralynx events."""
        if not analogSignalImported:
            self._recording = NeuralynxIO(self.experiment['directory'])
            self._ephysData = self._recording.read_block(signal_group_mode='split-all')
        unsortedEventLabels = []
        unsortedEventTimestamps = []
        self.NeuralynxEvents = {}
        for seg in self._ephysData.segments:
            for e in seg.events:
                for k, l in enumerate(e.labels.astype(str)):
                    unsortedEventLabels.append(l)
                    unsortedEventTimestamps.append(e.times[k].magnitude)
        # Sort all of the events
        npUnsortedEventLabels = np.array(unsortedEventLabels)
        npUnsortedEventTimestamps = np.array(unsortedEventTimestamps)
        evSortInds = np.argsort(npUnsortedEventTimestamps)
        self.NeuralynxEvents['labels'] = npUnsortedEventLabels[evSortInds]
        self.NeuralynxEvents['timestamps'] = npUnsortedEventTimestamps[evSortInds] - self.experiment['zero time (s)']


    def computeSpectrogram(self, channel='CBvsPFCEEG', windowLength=30, windowStep=3, freqLims=[0,50], bandwidth=2, plotSpectrogram=False, plotEvents=True):
        """Estimate (and plot) the multi-taper spectrogram of a specified EEG channel. Developed with code mostly from Morgan Siegmann."""
        fs = int(self.samplingRate[channel])
        windowLengthSamples = windowLength * fs
        windowStepSamples = windowStep * fs
        EEGMat = misc_Functions._overlapBinning(self.EEG[channel], windowLengthSamples, windowStepSamples)
        # Make a time vector
        tMat = misc_Functions._overlapBinning(self.tEEG[channel], windowLengthSamples, windowStepSamples)
        self.tSpect = tMat[:,windowLengthSamples // 2]
        PSDSpect, self.freqsSpect = psd_array_multitaper(EEGMat, fs, fmin=freqLims[0], fmax=freqLims[1], bandwidth=bandwidth)
        self.pSpect = np.transpose(10 * np.log10(PSDSpect))
        if plotSpectrogram:
            h, ax = misc_Functions.spectrogram(self.tSpect/60, self.freqsSpect, self.pSpect, xLabel='Time (min)')
            if plotEvents:
                misc_Functions.markEvents(ax, self.NeuralynxEvents['timestamps']/60)
        return h, ax


    def computePhase(self, channel):
        """Compute the instantaneous phase of a specified EEG channel."""
        analyticSignalEEG = hilbert(self.EEG[channel])
        self.instantaneousPhaseEEG = np.unwrap(np.angle(analyticSignalEEG))