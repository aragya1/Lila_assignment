import os
import pandas as pd
from data_processor import process_directory, process_file_like, is_human

print("Running Automated Checks on LILA_games codebase...\n")

# 1. Check Data Processor
base_dir = "/home/ok/LILA_games/player_data"
if os.path.exists(base_dir):
    print("Loading a subset of data to verify parsing...")
    # Just load one folder to save time, e.g. February_10
    subset_dir = os.path.join(base_dir, "February_14") # smallest folder
    df = process_directory(subset_dir)
    print(f"Loaded {len(df)} rows from February_14.")
    
    if not df.empty:
        # Verify event decoding
        assert type(df['event'].iloc[0]) == str, "Event column should be decoded to string"
        print("✅ Event column decoded successfully.")
        
        # Verify Human vs Bot logic
        assert 'is_bot' in df.columns, "is_bot column missing"
        human_sample = "f4e072fa-b7af-4761-b567-1d95b7ad0108"
        bot_sample = "1440"
        assert is_human(human_sample) == True, "UUID should be human"
        assert is_human(bot_sample) == False, "Numeric ID should be bot"
        print("✅ Human/Bot identification works.")

        # Verify Coordinate mapping exists and is not null
        assert 'pixel_x' in df.columns and 'pixel_y' in df.columns, "Pixel columns missing"
        assert not df['pixel_x'].isnull().all(), "Pixel coordinates are all null"
        print("✅ Coordinate mapping generated values.")

        # Verify Timeline logic
        assert 'match_time_sec' in df.columns, "Relative match time missing"
        assert df['match_time_sec'].min() == 0.0, "Match time should start at 0.0"
        print("✅ Match timeline logic verified.")
else:
    print("❌ player_data directory not found!")

# 2. Verify Deliverables
files_to_check = ["app.py", "ARCHITECTURE.md", "INSIGHTS.md", "README.md"]
for f in files_to_check:
    if os.path.exists(f"/home/ok/LILA_games/{f}"):
        print(f"✅ {f} exists.")
    else:
        print(f"❌ {f} is missing.")

print("\nAll programmatic checks complete.")
