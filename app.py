import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import io
import base64
import zipfile
from data_processor import process_directory, process_file_like

def get_image_base64(img):
    buffered = io.BytesIO()
    # Convert to RGB if necessary (e.g. for RGBA png to jpg, or just to be safe)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(buffered, format="JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

st.set_page_config(page_title="LILA Player Journey Visualization", layout="wide")

@st.cache_data
def load_base_data():
    base_dir = "player_data"
    if os.path.exists(base_dir):
        return process_directory(base_dir)
    return pd.DataFrame()

# Load base data
if 'df' not in st.session_state:
    with st.spinner("Loading base dataset..."):
        st.session_state.df = load_base_data()

st.title("🗺️ LILA BLACK - Player Journey Visualization")

# Sidebar - Upload Data
st.sidebar.header("📁 Upload New Data")
uploaded_files = st.sidebar.file_uploader(
    "Upload .zip or .nakama-0 files", 
    type=["zip", "nakama-0"], 
    accept_multiple_files=True
)

if uploaded_files and st.sidebar.button("Process Uploaded Files"):
    with st.spinner("Processing new data..."):
        new_frames = []
        for file in uploaded_files:
            if file.name.endswith(".zip"):
                with zipfile.ZipFile(file) as z:
                    for filename in z.namelist():
                        if filename.endswith(".nakama-0"):
                            with z.open(filename) as f:
                                df = process_file_like(io.BytesIO(f.read()))
                                if not df.empty:
                                    df['date'] = "Uploaded"
                                    new_frames.append(df)
            else:
                df = process_file_like(io.BytesIO(file.read()))
                if not df.empty:
                    df['date'] = "Uploaded"
                    new_frames.append(df)
                    
        if new_frames:
            new_df = pd.concat(new_frames, ignore_index=True)
            # Recalculate relative time for the new matches
            if 'ts' in new_df.columns:
                new_df['ts'] = pd.to_datetime(new_df['ts'])
                new_df['match_time_sec'] = new_df.groupby('match_id')['ts'].transform(lambda x: (x - x.min()).dt.total_seconds())
            
            st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
            st.sidebar.success(f"Added {len(new_df)} new events!")

# Sidebar - Filters
st.sidebar.header("🔍 Filters")
df = st.session_state.df

if df.empty:
    st.warning("No data loaded. Please upload data or ensure the player_data folder exists.")
    st.stop()

# 0. Global Match Search
st.sidebar.markdown("---")
search_query = st.sidebar.text_input("Search by Match ID", placeholder="Enter full or partial ID...")

if search_query:
    # Find all matches matching the query
    matching_matches = df[df['match_id'].str.contains(search_query, case=False, na=False)]['match_id'].unique()
    
    if len(matching_matches) > 0:
        selected_match = st.sidebar.selectbox("Matching Results", sorted(matching_matches))
        match_df = df[df['match_id'] == selected_match].copy()
        # Automatically detect map and date for the found match
        selected_map = match_df['map_id'].iloc[0]
        selected_date = match_df['date'].iloc[0]
        st.sidebar.info(f"Found match on **{selected_map}** ({selected_date})")
    else:
        st.sidebar.error("No match found for that ID.")
        st.stop()
else:
    # Standard Step-by-Step Filters
    # 1. Map Filter
    maps = sorted(df['map_id'].dropna().unique())
    selected_map = st.sidebar.selectbox("Select Map", maps)
    filtered_df = df[df['map_id'] == selected_map]

    # 2. Date Filter
    dates = sorted(filtered_df['date'].dropna().unique())
    selected_date = st.sidebar.selectbox("Select Date", dates)
    filtered_df = filtered_df[filtered_df['date'] == selected_date]

    # 3. Match Filter
    matches = sorted(filtered_df['match_id'].dropna().unique())
    selected_match = st.sidebar.selectbox("Select Match", matches)
    match_df = filtered_df[filtered_df['match_id'] == selected_match].copy()

# --- Timeline Slider (Moved Up) ---
st.sidebar.markdown("---")
st.sidebar.header("⏳ Match Playback")
if not match_df.empty:
    # Ensure we have match_time_sec
    if 'match_time_sec' not in match_df.columns and not match_df.empty:
        match_df['ts'] = pd.to_datetime(match_df['ts'])
        match_df['match_time_sec'] = (match_df['ts'] - match_df['ts'].min()).dt.total_seconds()
    
    max_time = float(match_df['match_time_sec'].max())
    if max_time > 0:
        current_time = st.sidebar.slider(
            "Time (seconds)", 
            min_value=0.0, 
            max_value=max_time, 
            value=max_time,
            step=1.0
        )
        match_df = match_df[match_df['match_time_sec'] <= current_time]
    else:
        st.sidebar.info("Single event match (no duration).")
st.sidebar.markdown("---")

# Sidebar - Event Toggles
st.sidebar.header("🎯 Events to Display")
show_human_pos = st.sidebar.checkbox("Human Positions", value=True)
show_bot_pos = st.sidebar.checkbox("Bot Positions", value=True)
show_kills = st.sidebar.checkbox("Kills (Human vs Human & Bot)", value=True)
show_deaths = st.sidebar.checkbox("Deaths", value=True)
show_loot = st.sidebar.checkbox("Loot Drops/Pickups", value=True)
show_storm = st.sidebar.checkbox("Storm Deaths", value=True)

# Heatmap Toggle
show_heatmap = st.sidebar.toggle("🔥 Show Density Heatmap", value=False)
st.sidebar.markdown("---")

# Load Minimap Image
image_path = f"player_data/minimaps/{selected_map}_Minimap.png"
if not os.path.exists(image_path):
    image_path = f"player_data/minimaps/{selected_map}_Minimap.jpg"

try:
    img = Image.open(image_path)
except Exception as e:
    st.error(f"Could not load minimap image for {selected_map}. Expected at {image_path}")
    st.stop()

# Visualization
st.subheader(f"Match Analysis: {selected_map}")
st.text(f"Match ID: {selected_match}")

fig = go.Figure()

if show_heatmap:
    # Build Heatmap
    events_for_heatmap = []
    if show_kills: events_for_heatmap.extend(['Kill', 'BotKill'])
    if show_deaths: events_for_heatmap.extend(['Killed', 'BotKilled'])
    if show_storm: events_for_heatmap.append('KilledByStorm')
    if show_loot: events_for_heatmap.append('Loot')
    if show_human_pos: events_for_heatmap.append('Position')
    if show_bot_pos: events_for_heatmap.append('BotPosition')
    
    heat_df = match_df[match_df['event'].isin(events_for_heatmap)]
    
    if not heat_df.empty:
        fig.add_trace(go.Histogram2dContour(
            x=heat_df['pixel_x'],
            y=heat_df['pixel_y'],
            colorscale='Hot',
            reversescale=False,
            opacity=0.6,
            ncontours=20,
            showscale=False,
            hovertemplate="<b>Density</b>: %{z} events<br><b>X</b>: %{x:.0f}<br><b>Y</b>: %{y:.0f}<extra></extra>"
        ))

else:
    # Build Scatter Points & Traces
    
    # 1. Human Paths
    if show_human_pos:
        human_pos = match_df[(match_df['event'] == 'Position') & (~match_df['is_bot'])]
        for user_id, group in human_pos.groupby('user_id'):
            fig.add_trace(go.Scatter(
                x=group['pixel_x'], y=group['pixel_y'],
                mode='lines+markers',
                name=f"Human Path ({str(user_id)[:6]})",
                line=dict(color='rgba(0, 200, 255, 0.5)', width=2),
                marker=dict(size=4, color='rgba(0, 200, 255, 0.5)'),
                hoverinfo='text',
                text=f"Human: {user_id}<br>Time: " + group['match_time_sec'].astype(str) + "s",
                showlegend=False
            ))
            
    # 2. Bot Paths
    if show_bot_pos:
        bot_pos = match_df[(match_df['event'] == 'BotPosition') & (match_df['is_bot'])]
        for user_id, group in bot_pos.groupby('user_id'):
            fig.add_trace(go.Scatter(
                x=group['pixel_x'], y=group['pixel_y'],
                mode='lines+markers',
                name=f"Bot Path ({user_id})",
                line=dict(color='rgba(255, 100, 0, 0.5)', width=2),
                marker=dict(size=4, color='rgba(255, 100, 0, 0.5)'),
                hoverinfo='text',
                text=f"Bot: {user_id}<br>Time: " + group['match_time_sec'].astype(str) + "s",
                showlegend=False
            ))
            
    # 3. Kills
    if show_kills:
        kills = match_df[match_df['event'].isin(['Kill', 'BotKill'])]
        fig.add_trace(go.Scatter(
            x=kills['pixel_x'], y=kills['pixel_y'],
            mode='markers',
            name="Kills",
            marker=dict(symbol='cross', size=12, color='green', line=dict(width=1, color='white')),
            hovertext=kills['event'] + " by " + kills['user_id'].astype(str)
        ))

    # 4. Deaths
    if show_deaths:
        deaths = match_df[match_df['event'].isin(['Killed', 'BotKilled'])]
        fig.add_trace(go.Scatter(
            x=deaths['pixel_x'], y=deaths['pixel_y'],
            mode='markers',
            name="Deaths",
            marker=dict(symbol='x', size=12, color='red', line=dict(width=1, color='white')),
            hovertext=deaths['event'] + " of " + deaths['user_id'].astype(str)
        ))

    # 5. Loot
    if show_loot:
        loot = match_df[match_df['event'] == 'Loot']
        fig.add_trace(go.Scatter(
            x=loot['pixel_x'], y=loot['pixel_y'],
            mode='markers',
            name="Loot",
            marker=dict(symbol='diamond', size=10, color='yellow', line=dict(width=1, color='black')),
            hovertext="Looted by " + loot['user_id'].astype(str)
        ))

    # 6. Storm Deaths
    if show_storm:
        storm = match_df[match_df['event'] == 'KilledByStorm']
        fig.add_trace(go.Scatter(
            x=storm['pixel_x'], y=storm['pixel_y'],
            mode='markers',
            name="Storm Death",
            marker=dict(symbol='circle-dot', size=14, color='purple', line=dict(width=2, color='white')),
            hovertext="Storm death: " + storm['user_id'].astype(str)
        ))

# Add the minimap as a background image
# In Plotly, y=0 is bottom by default. But we use yaxis range [1024, 0] (reversed).
# So 0 is the TOP of the plot. We want the image TOP to be at y=0.
img_base64 = get_image_base64(img)

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
        layer="below")
)

# Update layout: Range [0, 1024] for X, but [1024, 0] for Y to put 0 at the top.
fig.update_layout(
    xaxis=dict(showgrid=False, range=[0, 1024], visible=False),
    yaxis=dict(showgrid=False, range=[1024, 0], scaleanchor="x", scaleratio=1, visible=False),
    width=800,
    height=800,
    margin=dict(l=0, r=0, t=0, b=0),
    plot_bgcolor='black'
)

st.plotly_chart(fig, use_container_width=True)

# Data Table below map
with st.expander("View Raw Data for this Match"):
    st.dataframe(match_df[['ts', 'match_time_sec', 'user_id', 'is_bot', 'event', 'x', 'y', 'z', 'pixel_x', 'pixel_y']].sort_values('ts'))
