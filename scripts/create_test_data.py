import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path to import shared paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def truncate_neuralynx(input_path, output_path, record_size, num_records):
    # Neuralynx headers are always exactly 16384 bytes.
    with open(input_path, 'rb') as f_in:
        header = f_in.read(16384)
        records = f_in.read(record_size * num_records)
    
    with open(output_path, 'wb') as f_out:
        f_out.write(header)
        f_out.write(records)

src_ephys = PROJECT_ROOT / "sample data/2023-09-01_14-41-19-selected(1)"
dst_ephys = PROJECT_ROOT / "tests/data/sample_recording/UCLA and Neuralynx/ephys"
os.makedirs(dst_ephys, exist_ok=True)

# Generate small ephys dataset (approx 5 seconds of data)
# NCS record = 1044 bytes (512 samples per record). 32kHz sampling rate -> 62.5 records per second.
# 400 records = ~6.4 seconds
# NEV record = 104 bytes. 5000 records.

if os.path.exists(src_ephys):
    for f in os.listdir(src_ephys):
        src_file = os.path.join(src_ephys, f)
        dst_file = os.path.join(dst_ephys, f)
        
        if f.endswith(".ncs"):
            print(f"Truncating NCS: {f}")
            truncate_neuralynx(src_file, dst_file, 1044, 400)
        elif f.endswith(".nev"):
            print(f"Truncating NEV: {f}")
            truncate_neuralynx(src_file, dst_file, 104, 5000)
        elif f.endswith(".txt") or f.endswith(".nde"):
            print(f"Copying text config: {f}")
            shutil.copy(src_file, dst_file)
else:
    print(f"Skipping ephys, source folder not found at {src_ephys}")

src_mini = PROJECT_ROOT / "sample data/Miniscope-selected(1)"
dst_mini = PROJECT_ROOT / "tests/data/sample_recording/UCLA and Neuralynx/miniscope"
os.makedirs(dst_mini, exist_ok=True)

if os.path.exists(src_mini):
    print("Truncating Miniscope CSVs")
    with open(os.path.join(src_mini, "timeStamps.csv"), "r") as f:
        lines = f.readlines()
    with open(os.path.join(dst_mini, "timeStamps.csv"), "w") as f:
        f.writelines(lines[:101]) # Header + 100 frames

    if os.path.exists(os.path.join(src_mini, "headOrientation.csv")):
        with open(os.path.join(src_mini, "headOrientation.csv"), "r") as f:
            lines = f.readlines()
        with open(os.path.join(dst_mini, "headOrientation.csv"), "w") as f:
            f.writelines(lines[:101])

    print("Copying Miniscope metadata")
    if os.path.exists(os.path.join(src_mini, "metaData.json")):
        shutil.copy(os.path.join(src_mini, "metaData.json"), os.path.join(dst_mini, "metaData.json"))

    print("Truncating Miniscope AVI using FFmpeg")
    if os.path.exists(os.path.join(src_mini, "0.avi")):
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", os.path.join(src_mini, "0.avi"),
            "-frames:v", "100",
            "-c", "copy",
            os.path.join(dst_mini, "0.avi")
        ])
else:
    print(f"Skipping miniscope, source folder not found at {src_mini}")

print("Finished generating sample test fixtures!")
