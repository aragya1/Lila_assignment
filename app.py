import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import io
import base64
import zipfile
import time
from data_processor import process_directory, process_file_like

def get_image_base64(img):
    buffered = io.BytesIO()
    # Convert to RGB and compress as high-quality JPEG to keep it sharp but much smaller than PNG
    img.convert("RGB").save(buffered, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

# Page Configuration (Must be first Streamlit call)
# Using a fixed title to prevent the browser tab from "changing" or flickering during reruns
st.set_page_config(
    page_title="LILA Player Journey", 
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Hack: Hide Streamlit Branding (Ads/Footer/Menu) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            #stDecoration {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

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
                # Fix timestamp interpretation (seconds read as milliseconds)
                new_df['ts'] = pd.to_datetime(pd.to_datetime(new_df['ts']).astype('int64'), unit='s')
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

is_aggregate = False
match_df = pd.DataFrame()

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
    options = ["📊 ALL MATCHES (Aggregate View)"] + matches
    selected_match = st.sidebar.selectbox("Select Match", options)
    
    if selected_match == "📊 ALL MATCHES (Aggregate View)":
        is_aggregate = True
        match_df = filtered_df.copy()
    else:
        is_aggregate = False
        match_df = filtered_df[filtered_df['match_id'] == selected_match].copy()

# Reset playback state when switching matches
if 'current_match_id' not in st.session_state or st.session_state.current_match_id != selected_match:
    st.session_state.current_match_id = selected_match
    st.session_state.playing = False
    if not is_aggregate and not match_df.empty:
        st.session_state.playback_time = float(match_df['match_time_sec'].max())
    else:
        st.session_state.playback_time = 0.0
    st.session_state.map_x_range = [0, 1024]
    st.session_state.map_y_range = [1024, 0]

# --- Match Playback & Stats ---
st.sidebar.markdown("---")
st.sidebar.header("⏳ Match Playback")

if not match_df.empty:
    if is_aggregate:
        st.sidebar.info("💡 **Aggregate Mode:** Viewing patterns across all matches for this map/date. Playback is disabled.")
        
        # --- Aggregate Statistics Summary ---
        st.sidebar.markdown("### 📊 Event Summary")
        event_counts = match_df['event'].value_counts()
        
        # Mapping for cleaner display names
        display_names = {
            'Kill': '⚔️ Human Kills',
            'BotKill': '🤖 Bot Kills',
            'Killed': '💀 Human Deaths',
            'BotKilled': '🤖 Bot Deaths',
            'KilledByStorm': '🌪️ Storm Deaths',
            'Loot': '📦 Loot Pickups',
            'Position': '🚶 Human Movements',
            'BotPosition': '🤖 Bot Movements'
        }
        
        summary_data = []
        for event_type, count in event_counts.items():
            name = display_names.get(event_type, event_type)
            summary_data.append({"Event": name, "Count": count})
        
        if summary_data:
            st.sidebar.table(pd.DataFrame(summary_data).set_index('Event'))
        
        max_time = 0
    else:
        max_time = float(match_df['match_time_sec'].max())
        st.sidebar.write(f"Match Duration: {max_time:.1f}s | Events: {len(match_df)}")
        
        if max_time > 0:
            # Initialize playback state
            if 'playback_time' not in st.session_state:
                st.session_state.playback_time = max_time
            if 'playing' not in st.session_state:
                st.session_state.playing = False
            if 'last_play_time' not in st.session_state:
                st.session_state.last_play_time = None
            if 'playback_speed' not in st.session_state:
                st.session_state.playback_speed = 1.0

            # Playback Controls - Row 1
            col1, col2 = st.sidebar.columns(2)
            
            # Play / Pause Toggle
            play_label = "⏸️ Pause" if st.session_state.playing else "▶️ Play"
            if col1.button(play_label, use_container_width=True):
                # If we are at the end, restart automatically
                if not st.session_state.playing and st.session_state.playback_time >= max_time:
                    st.session_state.playback_time = 0.0
                
                st.session_state.playing = not st.session_state.playing
                if st.session_state.playing:
                    st.session_state.last_play_time = time.time()
                st.rerun()

            # Restart Button
            if col2.button("🔄 Restart", use_container_width=True):
                st.session_state.playback_time = 0.0
                st.session_state.playing = True
                st.session_state.last_play_time = time.time()
                st.rerun()

            # Playback Controls - Row 2 (Jump Buttons)
            col3, col4 = st.sidebar.columns(2)
            if col3.button("⏪ -10s", use_container_width=True):
                st.session_state.playback_time = max(0.0, st.session_state.playback_time - 10.0)
                st.rerun()
            if col4.button("⏩ +10s", use_container_width=True):
                st.session_state.playback_time = min(max_time, st.session_state.playback_time + 10.0)
                st.rerun()

            # Speed Selector
            st.session_state.playback_speed = st.sidebar.select_slider(
                "Playback Speed",
                options=[1.0, 1.25, 1.5, 2.0, 4.0],
                value=st.session_state.playback_speed,
                format_func=lambda x: f"x{x}"
            )

            # The Slider
            st.session_state.playback_time = st.sidebar.slider(
                "Time (seconds)", 
                0.0, max_time, st.session_state.playback_time, 1.0
            )
            match_df = match_df[match_df['match_time_sec'] <= st.session_state.playback_time]
        else:
            st.sidebar.info("Static match (no movement).")
else:
    st.sidebar.error("Selected match data is empty.")

st.sidebar.markdown("---")

# Sidebar - Event Toggles
st.sidebar.header("🎯 Events to Display")
# In aggregate mode, we default Human/Bot positions to false to keep it clean, but let user toggle them
show_human_pos = st.sidebar.checkbox("Human Positions", value=not is_aggregate)
show_bot_pos = st.sidebar.checkbox("Bot Positions", value=False)
show_kills = st.sidebar.checkbox("Kills (Human vs Human & Bot)", value=True)
show_deaths = st.sidebar.checkbox("Deaths", value=True)
show_loot = st.sidebar.checkbox("Loot Drops/Pickups", value=is_aggregate)
show_storm = st.sidebar.checkbox("Storm Deaths", value=True)

# Heatmap & Autofocus Toggles
col_a, col_b = st.sidebar.columns(2)
show_heatmap = col_a.toggle("🔥 Heatmap", value=is_aggregate)
show_autofocus = col_b.toggle("🎥 Autofocus", value=False, help="Automatically zoom to follow active players.")
st.sidebar.markdown("---")

# --- Viewport Logic (Persistence & Autofocus) ---
if not is_aggregate and show_autofocus and not match_df.empty:
    # Find most recent positions of all active entities to define the viewport
    recent_human = match_df[(match_df['event'] == 'Position') & (~match_df['is_bot'])].sort_values('ts').groupby('user_id').last()
    recent_bot = match_df[(match_df['event'] == 'BotPosition') & (match_df['is_bot'])].sort_values('ts').groupby('user_id').last()
    
    active_entities = pd.concat([recent_human, recent_bot])
    
    if not active_entities.empty:
        # Calculate bounding box with padding
        pad = 150
        min_x, max_x = active_entities['pixel_x'].min(), active_entities['pixel_x'].max()
        min_y, max_y = active_entities['pixel_y'].min(), active_entities['pixel_y'].max()
        
        # Apply padding and clamp to map bounds [0, 1024]
        st.session_state.map_x_range = [max(0, min_x - pad), min(1024, max_x + pad)]
        # Y is inverted in our coordinate system (0 is top)
        st.session_state.map_y_range = [min(1024, max_y + pad), max(0, min_y - pad)]
elif is_aggregate or (not show_autofocus and not st.session_state.get('playing', False)):
    # Reset to full map in aggregate mode or when stopped
    st.session_state.map_x_range = [0, 1024]
    st.session_state.map_y_range = [1024, 0]

# Map Static Mapping (Optimized Local Files)
MAP_OPTIMIZED_PATHS = {
    'AmbroseValley': "player_data/minimaps/AmbroseValley_optimized.jpg",
    'GrandRift':     "player_data/minimaps/GrandRift_optimized.jpg",
    'Lockdown':      "player_data/minimaps/Lockdown_optimized.jpg"
}

# Resolve Map Source (Pre-loaded for Plotly)
map_source = ""
local_path = MAP_OPTIMIZED_PATHS.get(selected_map, "")
if os.path.exists(local_path):
    try:
        img = Image.open(local_path)
        map_source = get_image_base64(img)
    except Exception:
        map_source = ""
else:
    map_source = ""

# Visualization
st.subheader(f"Match Analysis: {selected_map}")
st.text(f"Match ID: {selected_match}")

fig = go.Figure()

# --- Layer 1: Density Heatmap (Optional Overlay) ---
if show_heatmap:
    # Build Heatmap based on currently enabled toggles
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
            colorscale='YlOrRd', # Higher contrast for "Meat Grinders"
            reversescale=False,
            opacity=0.75, # Increased from 0.4 for better visibility
            ncontours=40, # More detail in the density clusters
            contours_coloring='heatmap', # Solid color fill for more "pop"
            showscale=False,
            hovertemplate="<b>Density</b>: %{z} events<br><b>X</b>: %{x:.0f}<br><b>Y</b>: %{y:.0f}<extra></extra>"
        ))

# --- Layer 2: Player Paths & Event Markers ---
# We collect Start/End markers separately to add them LAST (on top of everything)
start_end_markers = []

# 1. Human Paths
if show_human_pos:
    human_pos = match_df[(match_df['event'] == 'Position') & (~match_df['is_bot'])]
    # Group by both match and user to prevent lines jumping across matches
    groups = human_pos.groupby(['match_id', 'user_id'])
    colors = px.colors.qualitative.Plotly
    
    for i, ((m_id, u_id), group) in enumerate(groups):
        if group.empty: continue
        color = colors[i % len(colors)]
        
        # The Path
        fig.add_trace(go.Scatter(
            x=group['pixel_x'], y=group['pixel_y'],
            mode='lines',
            name=f"Human: {str(u_id)[:6]}" if not is_aggregate else "Human Path",
            line=dict(color=color, width=2 if is_aggregate else 3),
            opacity=0.3 if is_aggregate else 1.0,
            hoverinfo='text' if not is_aggregate else 'skip', # Disable snapping in aggregate
            text=f"Match: {m_id}<br>Human: {u_id}<br>Time: " + group['match_time_sec'].astype(str) + "s",
            showlegend=not is_aggregate or i == 0 # Only show one "Human Path" in legend if aggregate
        ))
        
        # Start/End Markers (Only for single match to keep aggregate clean)
        if not is_aggregate:
            start_end_markers.append(go.Scatter(
                x=[group['pixel_x'].iloc[0], group['pixel_x'].iloc[-1]], 
                y=[group['pixel_y'].iloc[0], group['pixel_y'].iloc[-1]],
                mode='markers',
                name=f"Start/End: {str(u_id)[:6]}",
                marker=dict(symbol=['triangle-right', 'square'], size=[15, 12], color=['lime', 'red'], line=dict(width=1, color='black')),
                showlegend=False
            ))
        
# 2. Bot Paths
if show_bot_pos:
    bot_pos = match_df[(match_df['event'] == 'BotPosition') & (match_df['is_bot'])]
    bot_groups = bot_pos.groupby(['match_id', 'user_id'])
    bot_colors = px.colors.qualitative.Pastel
    
    for i, ((m_id, u_id), group) in enumerate(bot_groups):
        if group.empty: continue
        color = bot_colors[i % len(bot_colors)]
        
        fig.add_trace(go.Scatter(
            x=group['pixel_x'], y=group['pixel_y'],
            mode='lines',
            name=f"Bot: {u_id}" if not is_aggregate else "Bot Path",
            line=dict(color=color, width=1 if is_aggregate else 2, dash='dot'),
            opacity=0.2 if is_aggregate else 1.0,
            hoverinfo='text' if not is_aggregate else 'skip',
            text=f"Match: {m_id}<br>Bot: {u_id}<br>Time: " + group['match_time_sec'].astype(str) + "s",
            showlegend=not is_aggregate or i == 0
        ))
        
        # Start/End for bots (Only for single match)
        if not is_aggregate:
            start_end_markers.append(go.Scatter(
                x=[group['pixel_x'].iloc[0], group['pixel_x'].iloc[-1]], 
                y=[group['pixel_y'].iloc[0], group['pixel_y'].iloc[-1]],
                mode='markers',
                marker=dict(symbol=['triangle-right', 'square'], size=[10, 8], color=['lime', 'red']),
                showlegend=False
            ))
            
# 3. Kills
if show_kills:
    kills = match_df[match_df['event'].isin(['Kill', 'BotKill'])]
    fig.add_trace(go.Scatter(
        x=kills['pixel_x'], y=kills['pixel_y'],
        mode='markers',
        name="Kills",
        marker=dict(
            symbol='cross', 
            size=8 if is_aggregate else 12, 
            color='green', 
            opacity=0.5 if is_aggregate else 1.0,
            line=dict(width=0.5 if is_aggregate else 1, color='white')
        ),
        hoverinfo='text' if not is_aggregate else 'skip',
        hovertext=kills['event'] + " by " + kills['user_id'].astype(str)
    ))

# 4. Deaths
if show_deaths:
    deaths = match_df[match_df['event'].isin(['Killed', 'BotKilled'])]
    fig.add_trace(go.Scatter(
        x=deaths['pixel_x'], y=deaths['pixel_y'],
        mode='markers',
        name="Deaths",
        marker=dict(
            symbol='x', 
            size=8 if is_aggregate else 12, 
            color='red', 
            opacity=0.5 if is_aggregate else 1.0,
            line=dict(width=0.5 if is_aggregate else 1, color='white')
        ),
        hoverinfo='text' if not is_aggregate else 'skip',
        hovertext=deaths['event'] + " of " + deaths['user_id'].astype(str)
    ))

# 5. Loot
if show_loot:
    loot = match_df[match_df['event'] == 'Loot']
    fig.add_trace(go.Scatter(
        x=loot['pixel_x'], y=loot['pixel_y'],
        mode='markers',
        name="Loot",
        marker=dict(
            symbol='diamond', 
            size=6 if is_aggregate else 10, # Smaller in aggregate to prevent overlap
            color='yellow', 
            opacity=0.4 if is_aggregate else 1.0, # Semi-transparent in aggregate
            line=dict(width=0.5 if is_aggregate else 1, color='black')
        ),
        hoverinfo='text' if not is_aggregate else 'skip',
        hovertext="Looted by " + loot['user_id'].astype(str)
    ))

# 6. Storm Deaths
if show_storm:
    storm = match_df[match_df['event'] == 'KilledByStorm']
    fig.add_trace(go.Scatter(
        x=storm['pixel_x'], y=storm['pixel_y'],
        mode='markers',
        name="Storm Death",
        marker=dict(
            symbol='circle-dot', 
            size=10 if is_aggregate else 14, 
            color='purple', 
            opacity=0.6 if is_aggregate else 1.0,
            line=dict(width=1 if is_aggregate else 2, color='white')
        ),
        hoverinfo='text' if not is_aggregate else 'skip',
        hovertext="Storm death: " + storm['user_id'].astype(str)
    ))

# --- FINAL LAYER: Start/End Markers ---
# We add these last so they appear on top of paths, kills, deaths, etc.
for marker in start_end_markers:
    fig.add_trace(marker)

# Add the background via base64 (now small and stable)
fig.add_layout_image(
    dict(
        source=map_source,
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

# Update layout with dynamic viewport (Autofocus or Full Map)
fig.update_layout(
    xaxis=dict(showgrid=False, range=st.session_state.map_x_range, visible=False),
    yaxis=dict(showgrid=False, range=st.session_state.map_y_range, scaleanchor="x", scaleratio=1, visible=False),
    width=900,
    height=800,
    margin=dict(l=0, r=150, t=30, b=0), # Added right margin for legend
    plot_bgcolor='black',
    uirevision=selected_match, # Preserves manual zoom/pan across reruns if requested range doesn't change
    hovermode='closest', # Ensures focus on what is directly under cursor
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.02,
        bgcolor="rgba(0, 0, 0, 0.5)",
        bordercolor="rgba(255, 255, 255, 0.3)",
        borderwidth=1,
        font=dict(size=12, color="white")
    )
)

st.plotly_chart(fig, use_container_width=True)

# Data Table below map
with st.expander("View Raw Data for this Match"):
    st.dataframe(match_df[['ts', 'match_time_sec', 'user_id', 'is_bot', 'event', 'x', 'y', 'z', 'pixel_x', 'pixel_y']].sort_values('ts'))

# Real-time Playback Loop (Executed AFTER rendering)
if 'playing' in st.session_state and st.session_state.playing:
    if not match_df.empty and not is_aggregate:
        # Use the max_time calculated before filtering at line 178
        if st.session_state.playback_time < max_time:
            # Calculate real-time elapsed since last run
            now = time.time()
            if st.session_state.last_play_time is not None:
                delta = (now - st.session_state.last_play_time) * st.session_state.playback_speed
                # Increment playback time by the real-time delta
                st.session_state.playback_time = min(st.session_state.playback_time + delta, max_time)
            
            st.session_state.last_play_time = now
            
            # Check if we reached the end
            if st.session_state.playback_time >= max_time:
                st.session_state.playing = False
                st.session_state.last_play_time = None
            
            # Balanced pause to prevent CPU pegging and reduce browser tab "flickering"
            # 0.1s provides a smooth 10fps update which is usually enough for telemetry
            time.sleep(0.1)
            st.rerun()
        else:
            st.session_state.playing = False
            st.session_state.last_play_time = None
    else:
        st.session_state.playing = False
        st.session_state.last_play_time = None
