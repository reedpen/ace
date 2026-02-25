#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V3 Miniscope Data Manager
"""
import csv
import json
import numpy as np
from src2.miniscope.miniscope_data_manager import MiniscopeDataManager
from src2.shared.path_finder import PathFinder
from src2.shared.exceptions import DataImportError

class V3MiniscopeDataManager(MiniscopeDataManager):
    """
    Handles V3 Miniscope data formats (metaData.json, timeStamps.csv, default events).
    """

    @classmethod
    def can_handle(cls, directory) -> bool:
        """Returns True if standard metaData.json is found in the directory."""
        from pathlib import Path
        dir_path = Path(directory)
        if not dir_path.exists():
            return False
        # Search for any metaData*.json or timeStamps*.csv
        return len(list(dir_path.rglob('metaData*.json'))) > 0 or len(list(dir_path.rglob('timeStamps*.csv'))) > 0

    def _get_miniscope_metadata(self) -> dict:
        """
        Imports miniscope metadata from a JSON file or multiple located at the paths returned by self._find_metadata_paths().
        """
        metadata_paths = self._find_metadata_paths()
        if not isinstance(metadata_paths, list):
            metadata_paths = [metadata_paths]
        print(f"Reading metadata from {metadata_paths}...")
        
        if metadata_paths[0] is None:
            print("No metadata paths found in your miniscope directory")
            return None
        
        metadata = None
        for metadata_path in metadata_paths:
            try:
                with open(metadata_path, 'r') as file:
                    if not metadata:
                        metadata = json.load(file)
                    else:
                        metadata = {**metadata, **json.load(file)}
            except (IOError, json.JSONDecodeError) as e:
                raise DataImportError(f"Error reading or parsing metadata file '{metadata_path}': {e}") from e
    
            # If 'frameRate' exists, try to convert it to a float
            if 'frameRate' in metadata:
                value = metadata['frameRate']
                try:
                    metadata['frameRate'] = float(value)
                except ValueError:
                    cleaned_value = value.replace('FPS', '').strip()
                    try:
                        metadata['frameRate'] = float(cleaned_value)
                    except ValueError:
                        raise ValueError(f"Unable to convert frameRate value '{value}' to float.")
        return metadata

    def _get_timestamps(self):
        """Load frame timestamps and numbers from CSV file."""
        file_path = self._find_timestamps_path()
        time_stamps = []
        frame_numbers = []
        with open(file_path, newline='') as t:
            next(t)
            reader = csv.reader(t)
            for row in reader:
                frame_numbers.append(int(row[0]))
                time_stamps.append(float(row[1]))
        time_stamps = np.divide(np.asarray(time_stamps), 1000)  # convert from ms to s
        return time_stamps, frame_numbers

    def _get_miniscope_events(self):
        """Import calcium imaging experiment events."""
        miniscope_events_filepaths = PathFinder.find(self.metadata['calcium imaging directory'], '.csv', 'notes')
        
        if miniscope_events_filepaths is not None and len(miniscope_events_filepaths) == 1:
            miniscope_events_filepath = str(miniscope_events_filepaths[0])
        elif miniscope_events_filepaths is not None and len(miniscope_events_filepaths) > 1:
            raise ValueError('Found multiple event files')
        else:
             # Just return empty if none so it doesn't crash if it's optional
            miniscope_events_filepath = None
            
        miniscope_events = {}
        miniscope_events['timestamps'] = []
        miniscope_events['labels'] = []
        
        if miniscope_events_filepath:
            try:
                with open(miniscope_events_filepath, newline='') as t:
                    next(t)
                    reader = csv.reader(t)
                    for row in reader:
                        miniscope_events['timestamps'].append(int(row[0]))
                        miniscope_events['labels'].append(row[1])
                miniscope_events['timestamps'] = np.divide(np.asarray(miniscope_events['timestamps']), 1000)  # converts from ms to s
            except (IOError, IndexError, ValueError, csv.Error) as e:
                print(f"Failed to extract events from notes.csv ({e}). Storing an empty dictionary...")
                
        return miniscope_events
