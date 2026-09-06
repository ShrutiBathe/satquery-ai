# SatQuery AI — Interactive AI Assistant for Multimodal Remote-Sensing Image Analysis

**Smart India Hackathon 2026** | **Problem Statement ID: SIH26167**

> **"Ask your satellite data anything."**  
> An industry-grade, multimodal AI geospatial intelligence frontend built in Python and Streamlit. Enables researchers, disaster response commanders, and non-experts to interrogate remote-sensing imagery using plain English natural-language queries.

---

## 🌟 Key Product Features

- ⚡ **Autonomous Task Selection (Auto Detect)**: Natural-language query parsing dynamically routes inquiries to the optimal specialist neural pipeline without requiring manual GIS workflow configuration.
- 🎯 **Visual Grounding & Localization**: Open-vocabulary localization of facilities, storage vessels, runways, and structures with sub-pixel spatial bounding boxes and segmentation contours.
- 🔄 **Bi-Temporal Change Detection**: Pair comparison across baseline and post-event dates with continuous radiometric difference heatmaps and high-confidence change masks.
- 📡 **Multimodal Optical + SAR Fusion**: Overcomes dense cloud and haze obscuration by fusing optical multispectral reflectance with weather-invariant Sentinel-1 C-Band synthetic aperture radar backscatter.
- 👁️ **Visual Question Answering (VQA)**: Deep scene comprehension, environmental inventory, and infrastructure auditing.
- 🔍 **Tri-Factor Confidence Decomposition**: Mathematical confidence decomposition into **Spatial Grounding**, **Semantic Category Alignment**, and **Radiometric Sensor Calibration**.
- 📊 **Autonomous Execution Trace**: 6-stage agent audit log displaying node latencies, model weights, and routing rationale.
- 💬 **Interactive Follow-up Chat**: Conversational thread allowing users to probe deeper into specific coordinates and anomaly details.
- 💾 **Insight Bookmarking & Comprehensive Exporting**: 1-click Markdown intelligence report and structured JSON payload exports.
- 🚀 **Zero-Friction Demo Mode**: Pre-packaged with 4 realistic procedural high-resolution satellite scenarios (Urban Growth, Petrochemical Storage Depot, Monsoon Flood Inundation, Maritime Harbor Operations) for instant offline evaluation.

---

## 🏗️ Architecture & Directory Structure

```
d:\SIH_PROJECT/
├── app.py                      # Main application entrypoint and view router
├── config/
│   ├── __init__.py
│   └── settings.py             # Design tokens, constants, and problem statement metadata
├── styles/
│   └── theme.css               # "Deep Orbit Geospatial" dark visual design system
├── components/
│   ├── __init__.py
│   ├── header.py               # HUD status bar and problem statement badge
│   ├── sidebar.py              # Navigation, demo mode toggle, system health HUD
│   ├── hero.py                 # Geospatial radar sweep HUD banner and CTAs
│   ├── cards.py                # 4 Specialist quick-analysis cards
│   ├── upload.py               # Single, Compare (A/B), and Optical+SAR uploaders
│   ├── query_input.py          # Query composer, prompt chips, and preflight summary
│   ├── workflow.py             # 7-stage autonomous pipeline visualizer & detected task HUD
│   ├── result_viewer.py        # Multi-tab visual evidence viewer (Original, Mask, Heatmap, BBox)
│   ├── evidence.py             # Ground truth legend and quantitative metrics table
│   ├── confidence.py           # Answer card and tri-factor confidence decomposition
│   ├── analysis_trace.py       # Expandable 6-stage agent execution trace
│   ├── follow_up.py            # Follow-up conversational inquiry component
│   ├── history.py              # Filterable session audit history with item management
│   ├── saved_insights.py       # Pinned discoveries gallery with report downloads
│   ├── api_docs.py             # System architecture & LangGraph/FastAPI backend contract
│   └── settings_view.py        # Inference thresholds and project metadata
├── services/
│   ├── __init__.py
│   ├── api_client.py           # Production backend contract (FastAPI / LangGraph REST client)
│   ├── mock_service.py         # High-fidelity simulation engine for Demo Mode
│   └── sample_data.py          # Procedural remote sensing raster generator
└── utils/
    ├── __init__.py
    ├── state.py                # Streamlit session state manager (prevents state loss)
    ├── validators.py           # Image format, dimension, and query validators
    ├── image_utils.py          # Bounding box projection, segmentation blending, diff heatmaps
    └── export_utils.py         # Markdown and JSON report generators
```

---

## 🚀 Running the Application

### 1. Ensure Dependencies Are Installed
```bash
pip install streamlit pillow opencv-python plotly numpy pandas requests
```

### 2. Launch Streamlit
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🔌 Connecting to Live AI Backend

By default, the application runs in **Demo Simulation Mode** (`demo_mode = True`), which enables instant evaluation with high-fidelity procedural satellite rasters.

To connect your live **FastAPI** or **LangGraph** backend:
1. Open the sidebar and toggle **Demo Simulation Mode** to **OFF** (or set `SATQUERY_BACKEND_URL` environment variable).
2. Ensure your backend implements the `POST /api/v1/analyze` endpoint specified in `components/api_docs.py`.
3. All requests and visual evidence layers conform to the contract defined in `services/api_client.py`.

