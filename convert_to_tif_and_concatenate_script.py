# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 16:07:33 2020

@author: Eric

For use in converting select .avi files to .tif files for preliminary analyses using Mesmerize.
"""

import miniscope

obj = miniscope.miniscope('settings_and_notes.dat')

obj.convertCaMovies(filenames=['msCam1.avi', 'msCam2.avi', 'msCam3.avi'])