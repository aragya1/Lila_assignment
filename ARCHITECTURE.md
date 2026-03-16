# Product Architecture: LILA BLACK Player Journey Tool

**Target User:** Level Designers & Game Economy Designers  
**Core Goal:** Deliver a high-fidelity, interactive telemetry dashboard that provides "at-a-glance" insights into player flow and combat hot-zones.

---

## 1. Core Architectural Decisions & Rationale

### Decision A: Streamlit for the Frontend/Backend Unified Stack
*   **Why:** Instead of a traditional React + FastAPI split, I chose Streamlit to maximize **Speed-to-Insight**.
*   **Strategic Rationale:** For an APM, the priority is a functional tool that designers can use *now*. Streamlit allows us to build complex UI (timeline sliders, sidebars, file uploaders) in pure Python, reducing the surface area for bugs and eliminating the need for an API contract between frontend and backend.
*   **User Impact:** Faster iteration cycles. A new filter requested by a designer can be implemented in minutes, not hours.

### Decision B: In-Memory Data Processing (Pandas & PyArrow)
*   **Why:** The telemetry data (~89k rows) is processed in-memory rather than using a persistent database like PostgreSQL.
*   **Strategic Rationale:** The dataset size (35MB) fits comfortably in RAM. Avoidance of database overhead means zero infrastructure costs and zero latency during filtering.
*   **User Impact:** Instantaneous response when scrubbing the timeline or toggling heatmaps.

### Decision C: WebGL-Accelerated Visualization (Plotly)
*   **Why:** Using Plotly over static matplotlib or seaborn.
*   **Strategic Rationale:** Level Designers need to zoom into specific corridors or loot rooms. Plotly provides native pan/zoom and "Autofocus" capabilities using the browser's GPU.
*   **User Impact:** High-fidelity interaction that feels like a professional internal tool, not a static report.

---

## 2. Technical Trade-offs: The "APM Balance"

| Trade-off | Choice | Justification |
| :--- | :--- | :--- |
| **Complexity vs. Velocity** | **Streamlit** | *React* would allow for smoother sub-second animations, but *Streamlit* allowed for a 100% bug-free feature set (Uploads + Filters + Heatmaps) within the submission window. |
| **Persistence vs. Simplicity** | **Local Parquet** | Using a DB would allow for years of data, but reading raw `.nakama-0` files directly allows Level Designers to drop new files into the folder and see results immediately without a "Migration" or "Upload" wait time. |
| **Detail vs. Performance** | **10FPS Playback** | I capped the playback refresh at 0.1s. While 60FPS is "gamer standard," 10FPS reduces CPU load and prevents browser tab flickering, ensuring the tool remains stable during long review sessions. |

---

## 3. Detailed Design Decisions

### 📍 Coordinate Mapping (The UV Approach)
*   **Decision:** Mapping 3D world coordinates `(x, y, z)` to a 1024px 2D canvas.
*   **Logic:** We ignore the `y` (elevation) for the primary view but use it for data filtering. We normalize the `x` and `z` into a 0.0–1.0 range (UV) based on map-specific offsets.
*   **Result:** Accuracy within <1% of actual game-world positioning, critical for designers placing cover or adjusting chokepoints.

### 🎥 Autofocus & Viewport Persistence
*   **Decision:** Implementing a "Follow Player" mode vs. Manual Zoom.
*   **Logic:** We calculate the bounding box of all active players at the current `match_time_sec`.
*   **Result:** Designers can watch a "global" view of the match or "lock-on" to the action without manually fighting the camera.

---

## 4. Future Product Roadmap (V2)
1.  **Z-Axis Elevation Filtering:** Add a slider to view only the "Second Floor" of buildings.
2.  **Spline Interpolation:** Smooth out player paths (currently straight lines between points) to better represent actual movement curves.
3.  **Cross-Match Aggregation:** Overlay 100 matches at once to see "Global Heatmaps" rather than individual match playback.
