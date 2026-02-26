import json
import os
import platform
import sys
import datetime
import time
import importlib.metadata
import numpy as np

class DiagnosticLogger:
    """Logs pipeline parameters, system versions, and diagnostic metrics to a JSON file."""
    def __init__(self, pipeline_name: str, line_num: int):
        self.pipeline_name = pipeline_name
        self.line_num = line_num
        self._start_time = time.time()
        self._total_paused_time = 0.0
        self._pause_start_time = None
        self.log_data = {
            "execution_info": {
                "pipeline": self.pipeline_name,
                "line_num": self.line_num,
                "timestamp_started": datetime.datetime.now().isoformat(),
                "timestamp_completed": None,
                "status": "Running"
            },
            "system_info": self._get_system_info(),
            "library_versions": self._get_library_versions(),
            "parameters": {},
            "data_metrics": {},
            "quality_control": {
                "dropped_frames": None,
                "missing_ttls_interpolated": 0,
                "errors": []
            }
        }
    
    def _get_system_info(self):
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": sys.version.split(' ')[0]
        }
        
    def _get_library_versions(self):
        libraries_to_check = ['numpy', 'scipy', 'neo', 'caiman', 'pandas', 'matplotlib']
        versions = {}
        for lib in libraries_to_check:
            try:
                versions[lib] = importlib.metadata.version(lib)
            except importlib.metadata.PackageNotFoundError:
                versions[lib] = "Not Installed"
        return versions

    def log_parameters(self, **kwargs):
        """Logs all arguments passed to the pipeline run method."""
        # Convert any non-serializable objects (like numpy arrays) to lists
        serializable_params = {}
        for k, v in kwargs.items():
            if isinstance(v, np.ndarray):
                serializable_params[k] = v.tolist()
            else:
                serializable_params[k] = v
        self.log_data["parameters"].update(serializable_params)

    def log_miniscope_metadata(self, miniscope_dm):
        """Extracts and logs relevant data from the MiniscopeDataManager."""
        if not miniscope_dm or not hasattr(miniscope_dm, 'metadata'):
            return
        
        self.log_data["data_metrics"]["miniscope"] = {
            "equipment": miniscope_dm.__class__.__name__,
            "directory": str(getattr(miniscope_dm, 'directory', miniscope_dm.metadata.get('calcium imaging directory', 'Unknown'))),
            "frame_rate": miniscope_dm.metadata.get('frameRate'),
            "total_frames": miniscope_dm.metadata.get('frames_total', None)
        }
        
        frames = self.log_data["data_metrics"]["miniscope"]["total_frames"]
        fr = self.log_data["data_metrics"]["miniscope"]["frame_rate"]
        if frames is not None and fr is not None and fr > 0:
            self.log_data["data_metrics"]["miniscope"]["recording_duration_seconds"] = float(frames) / float(fr)
            
        if miniscope_dm.coords:
            self.log_data["data_metrics"]["miniscope"]["crop_coords"] = miniscope_dm.coords
            
    def log_ephys_metadata(self, ephys_dm, channel_name: str = None):
        """Extracts and logs relevant data from the EphysDataManager."""
        if not ephys_dm or not hasattr(ephys_dm, 'channels'):
            return
            
        ephys_data = {
            "equipment": ephys_dm.__class__.__name__,
            "directory": str(getattr(ephys_dm, 'directory', 'Unknown')),
            "sampling_rate": None,
            "channel_analyzed": channel_name,
            "total_events": 0
        }
        
        # Try to get sampling rate from the specific channel or any available channel
        channel_to_check = None
        if hasattr(ephys_dm, 'channels'):
            if isinstance(ephys_dm.channels, dict):
                if channel_name and channel_name in ephys_dm.channels:
                    channel_to_check = ephys_dm.channels[channel_name]
                elif ephys_dm.channels:
                     channel_to_check = next(iter(ephys_dm.channels.values()))
            elif isinstance(ephys_dm.channels, list) and len(ephys_dm.channels) > 0:
                # Fallback if channels is just a flat list
                channel_to_check = ephys_dm.channels[0]
             
        if channel_to_check:
            ephys_data["sampling_rate"] = getattr(channel_to_check, 'sampling_rate', None)
            if hasattr(channel_to_check, 'events') and 'labels' in channel_to_check.events:
                ephys_data["total_events"] = len(channel_to_check.events['labels'])
                
            if hasattr(channel_to_check, 'time_vector') and channel_to_check.time_vector is not None and len(channel_to_check.time_vector) > 0:
                ephys_data["recording_duration_seconds"] = float(channel_to_check.time_vector[-1] - channel_to_check.time_vector[0])
            elif hasattr(channel_to_check, 'signal') and channel_to_check.signal is not None and ephys_data["sampling_rate"]:
                ephys_data["recording_duration_seconds"] = float(len(channel_to_check.signal)) / float(ephys_data["sampling_rate"])
                
        self.log_data["data_metrics"]["ephys"] = ephys_data

    def calculate_dropped_frames(self, channel, miniscope_dm, threshold=0.065):
        """
        Calculates dropped frames by comparing Miniscope timestamps to Ephys TTL pulses.
        Adapted from align_miniscope_ephys_utils.py
        """
        if not channel or not hasattr(channel, 'events') or 'labels' not in channel.events:
            self.log_error("Could not calculate dropped frames: Missing ephys events.")
            return

        frame_acq_idx = (channel.events['labels'] == 'TTL Input on AcqSystem1_0 board 0 port 0 value (0x0000).') | \
                        (channel.events['labels'] == 'TTL Input on AcqSystem1_0 board 0 port 0 value (0x0001).')
        
        tCaIm = channel.events['timestamps'][frame_acq_idx]
        
        if len(tCaIm) == 0:
            self.log_error("No camera TTL events found in ephys data.")
            return
            
        # Check for non-alternating TTLs (a sign of a hardware glitch)
        event_labels = channel.events['labels'][frame_acq_idx]
        alternating = [np.char.equal(event_labels[q+2], event_labels[q]) for q in range(0, len(event_labels)-2)]
        if len(event_labels) >= 2:
             alternating.append(np.char.not_equal(event_labels[-1], event_labels[-2]))
             
        if len(alternating) > 0 and sum(alternating) != (len(event_labels) - 1):
            self.log_data["quality_control"]["errors"].append("WARNING: TTL events do not alternate perfectly.")

        # Find gaps (dropped frames)
        dtCaIm = np.diff(tCaIm)
        idx_TTL_gap = np.where(dtCaIm > threshold)[0]
        
        total_dropped = 0
        if len(idx_TTL_gap) > 0 and 'frameRate' in miniscope_dm.metadata:
            frame_duration = 1.0 / miniscope_dm.metadata['frameRate']
            for gap_idx in idx_TTL_gap:
                # Calculate how many frames missing in this gap
                missing = round(dtCaIm[gap_idx] / frame_duration) - 1
                if missing > 0:
                    total_dropped += missing
                    
        self.log_data["quality_control"]["dropped_frames"] = int(total_dropped)
        self.log_data["quality_control"]["missing_ttls_interpolated"] = int(len(idx_TTL_gap))
        
    def pause_timer(self):
        if self._pause_start_time is None:
            self._pause_start_time = time.time()
            
    def resume_timer(self):
        if self._pause_start_time is not None:
            self._total_paused_time += time.time() - self._pause_start_time
            self._pause_start_time = None

    def log_error(self, error_msg: str):
        """Append a non-fatal error or warning to the log."""
        self.log_data["quality_control"]["errors"].append(error_msg)

    def save_log(self, output_dir: str):
        """Write the diagnostic dictionary to a JSON file."""
        run_duration_secs = time.time() - self._start_time - self._total_paused_time
        self.log_data["execution_info"]["run_duration_seconds"] = run_duration_secs
        self.log_data["execution_info"]["timestamp_completed"] = datetime.datetime.now().isoformat()
        
        # If no explicit errors and we reached the end, mark as Success
        if self.log_data["execution_info"]["status"] == "Running":
             self.log_data["execution_info"]["status"] = "Success"
             
        # Append diagnostic_logs to the provided output directory path
        output_dir = os.path.join(output_dir, "diagnostic_logs")
        os.makedirs(output_dir, exist_ok=True)
        
        safe_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diagnostic_log_{self.pipeline_name}_line{self.line_num}_{safe_time}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.log_data, f, indent=4)
            
        print(f"Saved diagnostic log to {filepath}")
        return filepath
