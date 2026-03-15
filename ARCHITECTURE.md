# Architecture: LILA BLACK - Player Journey Visualization Tool

## What was built and why
I built a **Unified Python Web Application** using **Streamlit**, **Pandas**, and **Plotly**.
- **Why Streamlit:** The assignment prioritizes a functional, polished tool for a Level Designer within a 10-15 hour limit. Streamlit allows rapid prototyping of data-heavy UI components (timeline sliders, file uploaders, filtering sidebars) without the overhead of maintaining a separate React frontend and Node.js/Python backend.
- **Why Pandas & PyArrow:** The `.nakama-0` files are small Parquet files. Pandas, powered by PyArrow, easily reads and aggregates these files directly in memory.
- **Why Plotly:** Plotly integrates seamlessly with Streamlit and provides robust, interactive WebGL-accelerated 2D scatter plots and density heatmaps that can be overlaid perfectly onto static minimap images.

## Data Flow
1. **Ingestion:** On initial load, the app traverses the `player_data` directory, reading all `.nakama-0` Parquet files. Users can also dynamically upload new `.zip` or `.nakama-0` files via the sidebar UI.
2. **Processing:** The `data_processor.py` script decodes byte-strings to text, flags `is_bot` by checking for UUIDs, and calculates a normalized `match_time_sec` (seconds elapsed since the first event of that match).
3. **Caching:** The combined Pandas DataFrame is stored in memory using Streamlit's `@st.cache_data`, ensuring lightning-fast subsequent filtering and rendering.
4. **Visualization:** When a map and match are selected, the data is filtered and passed to Plotly. The minimap image is set as the layout background, and events are drawn as specific markers and traces.

## Coordinate Mapping
The core challenge was mapping 3D game coordinates `(x, y, z)` onto a 1024x1024 2D minimap image.
- **Assumption:** The `y` coordinate represents vertical elevation and is ignored for the top-down 2D minimap.
- **Approach:**
  1. I converted the world `x` and `z` coordinates into a normalized UV range (0.0 to 1.0) by subtracting the map's origin offset and dividing by the map's scale. 
  `u = (x - origin_x) / scale`
  `v = (z - origin_z) / scale`
  2. I then scaled the UV coordinates up to the 1024 pixel canvas.
  `pixel_x = u * 1024`
  3. Because image origins (0,0) are at the top-left, but standard Cartesian coordinates (and UVs) increase upwards, the Y-axis pixel calculation is inverted.
  `pixel_y = (1 - v) * 1024`
This logic is vectorized using Pandas for maximum performance.

## Data Ambiguities & Assumptions
- **Assumption 1 (Incomplete Matches):** Some matches may be missing the very beginning or end (e.g., Feb 14 is a partial day). The `match_time_sec` is strictly relative to the *earliest timestamp observed* for that `match_id` in the dataset, which may not be the exact server start time, but serves perfectly for relative timeline visualization.
- **Assumption 2 (Overlapping Events):** At high zoom levels, multiple positions might overlap. I applied slight opacity (`rgba(..., 0.5)`) to paths so density becomes visually apparent even without the heatmap.

## Major Tradeoffs

| Alternative Considered | My Decision | Why |
| :--- | :--- | :--- |
| **React + FastAPI** | **Streamlit** | React+Deck.gl offers slightly smoother animations, but Streamlit allows for a feature-complete, bug-free, and highly maintainable single-codebase deliverable within the tight deadline. |
| **PostgreSQL / DuckDB** | **In-Memory Pandas (Cached)** | The dataset is extremely small (~89k rows, ~8MB). Setting up a separate database adds unnecessary deployment complexity. Pandas in RAM is significantly faster for this scale. |
| **Pre-processing Script** | **On-the-fly Processing** | Pre-processing into one big `.parquet` file would be faster on load, but doing it on-the-fly allows users to upload new raw zip files from the UI, directly satisfying future Level Designer needs. |

## What I'd do differently with more time
1. **Implement WebGL Map Rendering (Deck.gl):** With more time, I would wrap `deck.gl` inside a custom Streamlit component to handle highly fluid animations (e.g., watching dots move in real-time) rather than relying on a slider that redraws the Plotly chart.
2. **Path Interpolation:** Currently, position events are discrete straight lines. I would add spline interpolation to make player movements curve smoothly around obstacles.
3. **Z-axis (Elevation) Heatmaps:** The `y` coordinate is currently ignored. I would implement an altitude slider to filter events occurring only on the 2nd floor or roof of structures.
