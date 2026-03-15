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

# Sort by time
match_df = match_df.sort_values('ts')

# Discretize time into 2-second frames for the animation
match_df['frame'] = (match_df['match_time_sec'] // 2).astype(int) * 2

print(f"Match duration: {match_df['match_time_sec'].max():.1f}s, {len(match_df)} events")

# Load image
img_path = "player_data/minimaps/AmbroseValley_Minimap.png"
if not os.path.exists(img_path):
    img_path = "player_data/minimaps/AmbroseValley_Minimap.jpg"
img = Image.open(img_path)

buffered = io.BytesIO()
img.convert("RGB").save(buffered, format="JPEG", quality=60)
img_base64 = "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

print("Building Plotly Figure with animation frames...")
fig = px.scatter(
    match_df, 
    x="pixel_x", 
    y="pixel_y", 
    animation_frame="frame",
    animation_group="user_id", 
    color="is_bot",
    hover_name="event",
    range_x=[0, 1024], 
    range_y=[1024, 0] # Reversed Y
)

# Add background image
fig.add_layout_image(
    dict(
        source=img_base64,
        xref="x",
        yref="y",
        x=0,
        y=0,
        sizex=1024,
        sizey=1024,
        xanchor="left",
        yanchor="top",
        sizing="stretch",
        opacity=1,
        layer="below"
    )
)

fig.update_layout(
    xaxis=dict(showgrid=False, visible=False),
    yaxis=dict(showgrid=False, scaleanchor="x", scaleratio=1, visible=False),
    width=800,
    height=800,
    margin=dict(l=0, r=0, t=0, b=0),
    plot_bgcolor='black'
)

# Save to HTML 
out_file = "plotly_anim_test.html"
fig.write_html(out_file)
print(f"Saved test to {out_file}. You can open this in your browser.")
