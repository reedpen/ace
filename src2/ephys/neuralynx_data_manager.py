#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neuralynx Ephys Data Manager

Handles loading and processing Neuralynx .nev and .ncs files into Channel objects.
"""

import os
from neo.io import NeuralynxIO
from src2.ephys.ephys_data_manager import EphysDataManager
from src2.ephys.block_processor import BlockProcessor
from src2.shared.path_finder import PathFinder

class NeuralynxDataManager(EphysDataManager):
    """
    Manages the import of raw Neuralynx ephys data.
    """

    @classmethod
    def can_handle(cls, directory) -> bool:
        """Returns True if Neuralynx data files (.nev) are found in the directory."""
        from pathlib import Path
        dir_path = Path(directory)
        if not dir_path.exists():
            return False
        return len(list(dir_path.glob('*.nev'))) > 0 or len(list(dir_path.glob('Events.nev'))) > 0

    def import_ephys_block(self, ephys_directory):
        """Load raw Neuralynx data from disk into a Neo Block."""
        print('Importing raw Neuralynx ephys data...')
        ephys_file_path = self._find_ephys_file_path(ephys_directory)
        ephys_dir_path = os.path.dirname(ephys_file_path)
        file_reader = NeuralynxIO(dirname=ephys_dir_path)
        self.ephys_block = file_reader.read_block(signal_group_mode='split-all')

    def process_ephys_block_to_channels(self, channels=None, remove_artifacts=False):
        """Process raw ephys block data into Channel objects using BlockProcessor."""
        if self.ephys_block is None:
            raise ValueError("ephys_block is None. Must import data first.")
        
        processor = BlockProcessor(self.ephys_block, self.logger)
        new_channels = processor.process_raw_ephys(channels, remove_artifacts=remove_artifacts)
        for k, v in new_channels.items():
            self.channels[k] = v

    def _find_ephys_file_path(self, ephys_directory):
        """Find the Events.nev file in the ephys directory."""
        path_finder = PathFinder()
        events_path = path_finder.find( 
                        directory=ephys_directory,
                        suffix=".nev",
                        prefix="Events"
            )
        if not events_path:
            raise FileNotFoundError(f"Could not find Events.nev in {ephys_directory}")
        return events_path[0]
