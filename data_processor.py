import os
import pandas as pd
import pyarrow.parquet as pq
import uuid
import io

# Minimap configuration from README
MAP_CONFIGS = {
    'AmbroseValley': {'scale': 900, 'origin_x': -370, 'origin_z': -473},
    'GrandRift': {'scale': 581, 'origin_x': -290, 'origin_z': -290},
    'Lockdown': {'scale': 1000, 'origin_x': -500, 'origin_z': -500},
}

def is_human(user_id):
    """Check if a user_id is a UUID (Human) or numeric (Bot)."""
    try:
        uuid.UUID(str(user_id))
        return True
    except ValueError:
        return False

def process_file_like(file_obj):
    """Process a single parquet file or file-like object."""
    try:
        table = pq.read_table(file_obj)
        df = table.to_pandas()
    except Exception as e:
        print(f"Error reading file: {e}")
        return pd.DataFrame()
    
    if df.empty:
        return df

    # Decode event column from bytes
    df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x))
    
    # Identify bots vs humans
    df['is_bot'] = ~df['user_id'].apply(is_human)

    # Vectorized coordinate mapping
    dfs = []
    for map_id, group in df.groupby('map_id'):
        config = MAP_CONFIGS.get(map_id)
        if config:
            u = (group['x'] - config['origin_x']) / config['scale']
            v = (group['z'] - config['origin_z']) / config['scale']
            group['pixel_x'] = u * 1024
            group['pixel_y'] = (1 - v) * 1024
        else:
            group['pixel_x'] = None
            group['pixel_y'] = None
        dfs.append(group)
        
    if dfs:
        df = pd.concat(dfs, ignore_index=True)

    return df

def process_directory(base_dir):
    """Process all data in the player_data directory."""
    frames = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith('.nakama-0'):
                filepath = os.path.join(root, f)
                df = process_file_like(filepath)
                if not df.empty:
                    # Extract date from folder name
                    folder_name = os.path.basename(root)
                    if folder_name.startswith('February_'):
                        df['date'] = folder_name.replace('_', ' ')
                    else:
                        df['date'] = 'Unknown'
                    frames.append(df)
                    
    if not frames:
        return pd.DataFrame()
        
    full_df = pd.concat(frames, ignore_index=True)
    
    # Convert timestamp and calculate relative match time
    full_df['ts'] = pd.to_datetime(full_df['ts'])
    full_df['match_time_sec'] = full_df.groupby('match_id')['ts'].transform(lambda x: (x - x.min()).dt.total_seconds())
    
    return full_df
