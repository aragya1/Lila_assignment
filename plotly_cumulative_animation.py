import pandas as pd
import plotly.express as px
from PIL import Image
import os
import io
import base64
from data_processor import process_directory

print("Loading data...")
df = process_directory("player_data")
# Filter to just one match on AmbroseValley for testing
match_id = "5a081fe4-9dfd-4fdc-bdb8-68b57b856b7c.nakama-0" 
match_df = df[df['match_id'] == match_id].copy()
match_df = match_df.sort_values('ts')

# 1. Create discrete frames (5-second buckets to keep data size reasonable)
frame_size = 5
match_df['frame_bucket'] = (match_df['match_time_sec'] // frame_size).astype(int) * frame_size
unique_frames = sorted(match_df['frame_bucket'].unique())

print(f"Expanding dataset for cumulative animation. Frames: {len(unique_frames)}")

# 2. Expand the dataframe so frame N contains all data from 0 to N
# This is O(N^2) data expansion, so we keep the number of frames limited.
expanded_list = []
for f in unique_frames:
    # Filter for all data up to this frame
    snapshot = match_df[match_df['frame_bucket'] <= f].copy()
    snapshot['animation_frame'] = f
    expanded_list.append(snapshot)

full_anim_df = pd.concat(expanded_list, ignore_index=True)

# 3. Load background image
img_path = "player_data/minimaps/AmbroseValley_Minimap.png"
if not os.path.exists(img_path):
    img_path = "player_data/minimaps/AmbroseValley_Minimap.jpg"
img = Image.open(img_path)
buffered = io.BytesIO()
img.convert("RGB").save(buffered, format="JPEG", quality=50)
img_base64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

print("Building Cumulative Plotly Figure...")
# We use px.line so the trail is visible. 
# We add markers so discrete events (Kills, Loot) are still visible.
fig = px.line(
    full_anim_df, 
    x="pixel_x", 
    y="pixel_y", 
    animation_frame="animation_frame",
    color="is_bot",
    line_group="user_id",
    hover_name="event",
    markers=True,
    range_x=[0, 1024], 
    range_y=[1024, 0],
    labels={"is_bot": "Entity Type (True=Bot)"}
)

fig.add_layout_image(
    dict(
        source=img_base64,
        xref="x", yref="y",
        x=0, y=0,
        sizex=1024, sizey=1024,
        xanchor="left", yanchor="top",
        sizing="stretch",
        opacity=1, layer="below"
    )
)

fig.update_layout(
    xaxis=dict(showgrid=False, visible=False),
    yaxis=dict(showgrid=False, scaleanchor="x", scaleratio=1, visible=False),
    width=900, height=900,
    margin=dict(l=0, r=0, t=0, b=0),
    plot_bgcolor='black'
)

# Fix for Plotly animation stutter: maintain constant axis ranges
fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 100
fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 0

out_file = "plotly_cumulative_test.html"
fig.write_html(out_file)
print(f"Saved cumulative test to {out_file}. Open this in your browser.")
