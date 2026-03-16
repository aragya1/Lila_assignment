# LILA BLACK - Player Journey Visualization Tool

**🚀 Live Demo:** [lilaaragya.streamlit.app](https://lilaaragya.streamlit.app/)
**Github link:** https://github.com/aragya1/Lila_assignment.git

This tool provides an interactive, web-based visualization of player telemetry data for LILA BLACK. It allows Level Designers to view player paths, combat events, and heatmaps overlaid on game minimaps.

## Features
- **Dynamic Uploads:** Upload new `.nakama-0` parquet files or `.zip` archives directly from the browser.
- **Interactive Timeline:** Scrub through a match to see events unfold over time, with speed control settings and +- 10 second
- **Filtering:** Isolate data by Map, Date, and Match ID.
- **Heatmaps:** Toggle density heatmaps to identify high-traffic areas and kill zones.
- **Visual Clarity:** Distinct markers for Kills, Deaths, Loot, and Storm deaths. Differentiated paths for Humans vs. Bots.

## Tech Stack
- **Python 3.12+**
- **Streamlit** (Frontend & UI)
- **Pandas & PyArrow** (Data Processing)
- **Plotly** (Map Visualization)

## Local Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/aragya1/Lila_assignment.git
   cd Lila_assignment
   ```

2. **Set up a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure Data is Present**
   Make sure the `player_data/` folder (containing the `.nakama-0` files and the `minimaps/` folder) is located in the root directory of this project.

5. **Run the Application**
   ```bash
   streamlit run app.py
   ```

6. **View in Browser**
   Open your browser and navigate to `http://localhost:8501`.
