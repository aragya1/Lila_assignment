import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os
import io
import base64
import time
from data_processor import process_directory, process_file_like

st.set_page_config(page_title="LILA Pro - High Fidelity Visualization", layout="wide")

def get_image_base64(img):
    buffered = io.BytesIO()
    # Convert to RGB and compress to keep the browser payload manageable
    img.convert("RGB").save(buffered, format="JPEG", quality=70)
    return "data:image/jpeg;base64," + base64.b64encode(buffered.getvalue()).decode()

@st.cache_data
def load_base_data():
    base_dir = "player_data"
    if os.path.exists(base_dir):
        return process_directory(base_dir)
    return pd.DataFrame()

if 'df' not in st.session_state:
    with st.spinner("Loading base dataset..."):
        st.session_state.df = load_base_data()

st.title("🚀 LILA BLACK - Animated Player Journey")

# --- Sidebar Filters ---
df = st.session_state.df
if df.empty:
    st.error("Data directory not found. Please ensure 'player_data' is present.")
    st.stop()

st.sidebar.header("🔍 Select Match")
maps = sorted(df['map_id'].dropna().unique())
selected_map = st.sidebar.selectbox("Select Map", maps)
filtered_df = df[df['map_id'] == selected_map]

dates = sorted(filtered_df['date'].dropna().unique())
selected_date = st.sidebar.selectbox("Select Date", dates)
filtered_df = filtered_df[filtered_df['date'] == selected_date]

matches = sorted(filtered_df['match_id'].dropna().unique())
selected_match = st.sidebar.selectbox("Select Match", matches)
match_df = filtered_df[filtered_df['match_id'] == selected_match].copy()
match_df = match_df.sort_values('ts')

st.sidebar.markdown("---")
frame_step = st.sidebar.slider("Animation Detail (Step size)", 2, 20, 10, help="Lower step size = smoother animation but slower load.")

if st.sidebar.button("🎬 Generate Smooth Animation"):
    with st.spinner("Preparing high-fidelity frames... This may take a few seconds for long matches."):
        # 1. Bucket time into frames
        match_df['frame'] = (match_df['match_time_sec'] // frame_step).astype(int) * frame_step
        unique_frames = sorted(match_df['frame'].unique())
        
        # 2. Define Event Styling
        event_styles = {
            'Kill':       {'color': '#00FF00', 'symbol': 'cross',       'size': 14, 'name': 'Kill (H)'},
            'BotKill':    {'color': '#90EE90', 'symbol': 'cross',       'size': 12, 'name': 'Kill (B)'},
            'Killed':     {'color': '#FF0000', 'symbol': 'x',           'size': 14, 'name': 'Death (H)'},
            'BotKilled':  {'color': '#FF4500', 'symbol': 'x',           'size': 12, 'name': 'Death (B)'},
            'Loot':       {'color': '#FFFF00', 'symbol': 'diamond',     'size': 10, 'name': 'Loot'},
            'KilledByStorm': {'color': '#A020F0', 'symbol': 'circle-x', 'size': 16, 'name': 'Storm Death'},
        }

        # 3. Create Frames manually with graph_objects for cumulative trail effect
        frames = []
        for i, f in enumerate(unique_frames):
            snapshot = match_df[match_df['frame'] <= f]
            data_traces = []
            
            # Trace A: Human Paths (Lines)
            humans = snapshot[~snapshot['is_bot']]
            for uid, group in humans.groupby('user_id'):
                data_traces.append(go.Scatter(
                    x=group['pixel_x'], y=group['pixel_y'],
                    mode='lines', line=dict(color='rgba(0, 255, 255, 0.4)', width=2),
                    showlegend=False, hoverinfo='skip'
                ))

            # Trace B: Bot Paths (Lines)
            bots = snapshot[snapshot['is_bot']]
            for uid, group in bots.groupby('user_id'):
                data_traces.append(go.Scatter(
                    x=group['pixel_x'], y=group['pixel_y'],
                    mode='lines', line=dict(color='rgba(255, 165, 0, 0.3)', width=1),
                    showlegend=False, hoverinfo='skip'
                ))

            # Trace C: Discrete Events (Symbols) - only show events up to now
            for evt_type, style in event_styles.items():
                evt_df = snapshot[snapshot['event'] == evt_type]
                if not evt_df.empty:
                    data_traces.append(go.Scatter(
                        x=evt_df['pixel_x'], y=evt_df['pixel_y'],
                        mode='markers',
                        name=style['name'],
                        # Use first occurrence to set legend label only once
                        legendgroup=evt_type,
                        showlegend=(i == 0), 
                        marker=dict(symbol=style['symbol'], size=style['size'], color=style['color'], line=dict(width=1, color='white')),
                        hovertext=evt_df['user_id']
                    ))
            
            frames.append(go.Frame(data=data_traces, name=str(f)))

        # 4. Build Initial Figure (using frame 0)
        initial_traces = frames[0].data if frames else []
        fig = go.Figure(
            data=initial_traces,
            layout=go.Layout(
                xaxis=dict(range=[0, 1024], visible=False, autorange=False),
                yaxis=dict(range=[1024, 0], visible=False, autorange=False, scaleanchor="x", scaleratio=1),
                updatemenus=[{
                    "type": "buttons",
                    "buttons": [
                        {"label": "▶️ Play", "method": "animate", "args": [None, {"frame": {"duration": 150, "redraw": False}, "fromcurrent": True}]},
                        {"label": "⏸️ Pause", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}]}
                    ],
                    "direction": "left", "pad": {"r": 10, "t": 87}, "showactive": False, "x": 0.1, "xanchor": "right", "y": 0, "yanchor": "top"
                }],
                sliders=[{
                    "active": 0, "yanchor": "top", "xanchor": "left",
                    "currentvalue": {"font": {"size": 20}, "prefix": "Match Time: ", "visible": True, "suffix": "s", "xanchor": "right"},
                    "transition": {"duration": 300, "easing": "cubic-in-out"},
                    "pad": {"b": 10, "t": 50}, "len": 0.9, "x": 0.1, "y": 0,
                    "steps": [{"args": [[f.name], {"frame": {"duration": 300, "redraw": False}, "mode": "immediate", "transition": {"duration": 300}}],
                               "label": f.name, "method": "animate"} for f in frames]
                }],
                width=1000, height=1000, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor='black'
            ),
            frames=frames
        )

        # 5. Add Map Image
        image_path = f"player_data/minimaps/{selected_map}_Minimap.png"
        if not os.path.exists(image_path): image_path = f"player_data/minimaps/{selected_map}_Minimap.jpg"
        img = Image.open(image_path)
        img_base64 = get_image_base64(img)
        
        fig.add_layout_image(dict(
            source=img_base64, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024,
            xanchor="left", yanchor="top", sizing="stretch", opacity=1, layer="below"
        ))

        st.plotly_chart(fig, use_container_width=True)
        st.success(f"Generated {len(frames)} frames for match {selected_match}")

with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. Select a Match from the sidebar.
    2. Adjust the **Animation Detail** slider (lower is smoother but slower to load).
    3. Click **Generate Smooth Animation**.
    4. Use the **Play/Pause** buttons or the bottom **Slider** to explore the timeline.
    """)
