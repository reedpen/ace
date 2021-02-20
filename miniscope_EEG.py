# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 19:54:58 2020

@author: eric
"""

# import csv
import EEG
import miniscope
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['svg.fonttype'] = 'none'
import misc_Functions

class miniscopeEEG(EEG.NeuralynxEEG, miniscope.miniscope):
    """This is the class definition for handling miniscopes and simultaneous EEG data."""
    def __init__(self, lineNum, filename='experiments.csv', filenameMiniscope='miniscope_settings_and_notes.dat'):
        super().__init__(filenameMiniscope=filenameMiniscope, lineNum=lineNum, filename=filename)


    def importEvents(self):
        """Translate the events imported from self.experiment['Miniscope settings filename']
        into a common time as the Neuralynx time format and combine the events from the two sources."""
        pass


    def _syncCaMovieTimes(self, channel):
        """Create time vector for calcium movies from TTL events in Neuralynx."""
        frameAcqIdx = (self.NeuralynxEvents['labels'] == 'TTL Input on AcqSystem1_0 board 0 port 0 value (0x0000).') | (self.NeuralynxEvents['labels'] == 'TTL Input on AcqSystem1_0 board 0 port 0 value (0x0001).')
        self.tCaIm = np.nan * np.ones(np.shape(frameAcqIdx))
        for k, caImEvent in enumerate(self.NeuralynxEvents['timestamps'][frameAcqIdx]):
            self._tIdxCaIm[k] = (self.tEEG[channel] - caImEvent).argmin()
        self.tCaIm = self.tEEG[channel][self._tIdxCaIm]


    def _phaseCaEvents(self, channel, neuron, syncToEEGChannel):
        """Compare calcium events to the phase extracted from a specified EEG channel."""
        self._syncCaMovieTimes(channel)
        phaseEEG = self.computePhase(channel)
        if neuron == 'all':
            self.CaEventsPhases = phaseEEG[:]#########FILL IN LATER
        elif type(neuron) == int:
            self.CaEventsPhases = phaseEEG[:]#########FILL IN LATER


    def phaseCaEventsHistogram(self, channel='CBvsPFCEEG', neuron='all', bins=18, plotHistogram=False):
        """Compute the histogram of calcium events vs phase.
        CHANNEL is the channel to compare the timing of calcium events to.
        NEURON is a list of the neuron indexes to compare. All neurons can be selected with 'all'.
        PLOTHISTOGRAM chooses whether or not to plot the computed histogram."""
        self._phaseCaEvents(channel, neuron)
        if plotHistogram:
            plt.figure()
            ax = misc_Functions.prepAxes(xLabel='Phase (rad)', yLabel='Event Count')
            self.hist, self.binEdges = ax.hist(self.CaEventsPhases, bins=bins)
        else:
            self.hist, self.binEdges = np.histogram(self.CaEventsPhases, bins=bins)


    def phaseCaEventsPolarPlot(self, channel='CBvsPFCEEG', neuron='all', bins=18, plotMeanVector=True):
        """"""
        pass