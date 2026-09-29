# CragTrip — Climbing Trip Concierge & Logistics Engine

![CragTrip Demo](cragtrip_demo.gif)

**CragTrip** is an AI agent built on the Google Agent Development Kit (ADK) and Agent Engine. It acts as an expert rock climbing concierge that helps climbers discover outdoor climbing destinations across Europe (Germany, Austria, Switzerland, France), inspect routes and topos, check live weather, calculate road logistics and tolls, generate scenic crag artwork, compile shareable trip brochure PDFs, and remember personal climbing preferences and vehicle specs across sessions.

---

## What the Agent Actually Implements

Based on the codebase in `app/` and the tools wired to `root_agent`:

### 1. Crag & Topo Database (Google Cloud Firestore)
- **Crag Discovery & Filtering (`list_crags`)**: Streams climbing crags from the `crags` Firestore collection with optional filters by climbing discipline (sport climbing, trad climbing, bouldering) and country.
- **Topos, Accommodations & Details (`get_crag_details`)**: Retrieves comprehensive crag records including sectors, route lists with difficulties (French and Yosemite decimal grades), topos, approaches, and nearby campsites/huts/apartments.
- **Interactive Clickable Descriptions**: All crag and accommodation names/descriptions are linked with direct Google Maps search URLs, allowing climbers to tap any crag, campground, gîte, or alpine refuge directly from chat bubbles and A2UI cards.
- **Crag Contribution (`add_or_update_crag`)**: Allows climbers to add or update crag records in Firestore.
- **Vehicle Profiles (`save_user_vehicle_profile`, `get_user_vehicle_profile`)**: Persists the user's vehicle fuel consumption (L/100km), climber passenger capacity, and gear storage notes in the `user_profiles` Firestore collection.

### 2. Live Weather & Climbing Conditions (`get_crag_weather`)
- Fetches real-time atmospheric data (temperature, humidity, precipitation, wind speed, friction index) and multi-day forecasts for European crag destinations to evaluate rock conditions.

### 3. Road Travel Logistics & Toll Calculator (`calculate_travel_logistics`)
- Calculates driving distance and travel times from origin cities (Munich, Zurich, Paris, Innsbruck, Frankfurt, etc.) to climbing destinations.
- Computes individualized fuel consumption and costs by fetching the user's vehicle specs from Firestore.
- Calculates required highway permits and toll roads:
  - **Austria**: 10-day Autobahn vignette (€11.50) + special tolls (Brenner, Tauern passes).
  - **Switzerland**: Annual motorway vignette (CHF 40 / ~€42).
  - **France**: Autoroute toll calculations.
- Evaluates carpool passenger/gear capacity and optional car rental cost estimates.

### 4. Shareable Trip Itinerary PDF Publishing (Google Cloud Storage)
- **Trip Asset Compiler (`compile_trip_itinerary_asset`)**: Builds publication-ready climbing trip brochures featuring destination maps, sector photos, classic routes, weather forecasts, toll logistics, and gear checklists.
- **Default Clickable PDF Link**: Automatically invoked during trip planning conversations, rendering a direct, styled download badge (`[Download Trip Brochure (PDF)](https://storage.googleapis.com/...)`) directly in the agent's output.
- **Cloud Storage Upload**: Uploads the generated PDF asset to a Google Cloud Storage media bucket (`gs://cragtrip-media-xxl67u`) and returns a public HTTPS link (`https://storage.googleapis.com/...`). Supports English, German, and Russian language outputs.

### 5. Scenic Visual Generation (Gemini 3.1 Flash Lite Image)
- **Crag Visualizer (`generate_crag_visual`)**: Generates climbing visualizations and approach sketches using the `gemini-3.1-flash-lite-image` model in the global region.
- **Artifacts & Public Bucket Integration**: Saves the generated image bytes to ADK session artifacts via `tool_context.save_artifact` (visible in the Playground panel) and uploads directly to Google Cloud Storage to return a public HTTPS URL.

### 6. Long-Term Cross-Session Memory (Vertex AI Memory Bank)
- **Preload Memory (`PreloadMemoryTool`)**: Injects relevant past facts, preferences, gear inventory, and climbing history into the agent's context at the start of each turn.
- **Memory Callback (`after_agent_callback=generate_memories_callback`)**: Automatically sends turn conversations to Vertex AI Memory Bank (`VertexAiMemoryBankService`) to extract and persist user facts across conversations.

### 7. Sandboxed Python Code Execution (Agent Engine Sandbox)
- **Sandbox Executor (`AgentEngineSandboxCodeExecutor`)**: Securely executes Python in an isolated Agent Engine sandbox environment to perform route difficulty calculations, pack weight optimizations, and custom calculations.

### 8. Rich Display Cards & Interactive Link Renderer (A2UI v0.8)
- Emits structured A2UI v0.8 JSON components (`Card`, `Column`, `Row`, `Text`, `Image`, `Divider`) via `a2ui_callback` (`after_model_callback`) so replies render as styled cards.
- The custom frontend includes a rich Markdown & URL parser that transforms markdown links and raw URLs inside chat bubbles and A2UI text components into interactive anchors and dedicated PDF badge buttons.

---

## Project Structure

```
crag-trip-agent/
├── app/
│   ├── agent.py               # Main agent definition, tools, and system prompt
│   ├── a2ui_utils.py          # A2UI callback and JSON response wrapper
│   ├── fast_api_app.py        # Local and deployed FastAPI serving interface
│   └── app_utils/
│       └── services.py        # Vertex AI Memory Bank, Session, and Artifact services
├── frontend/
│   ├── main.py                # FastAPI proxy communicating over A2A protocol
│   ├── requirements.txt       # Frontend dependencies
│   └── static/
│       └── index.html         # Responsive climbing-themed chat UI with A2UI renderer
├── agents-cli-manifest.yaml   # Deployment manifest targeting Agent Runtime (A2A)
├── pyproject.toml             # Python dependencies and package metadata
├── cragtrip_demo.gif          # Looping demo recording of CragTrip in action
└── README.md                  # Project documentation
```

---

## Local Setup & Run Instructions

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud SDK (`gcloud`) authenticated with Application Default Credentials:
  ```bash
  gcloud auth application-default login
  ```

### 1. Install Dependencies
```bash
uv sync
```

### 2. Run with ADK Web (Local Playground)
To launch the agent locally with cross-session Memory Bank support:
```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<YOUR_AGENT_ENGINE_ID>
```

### 3. Run the Custom Web Frontend Locally
To test the custom Alpine-themed chat UI connected to your agent runtime:
```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<ENGINE_ID>"
export AGENT_DIRECTORY="app"
uv run python3 frontend/main.py
```

---

## Deployment Summary

- **Agent Runtime**: Deployed via `agents-cli deploy` to Google Cloud Agent Platform (Agent Runtime) using the Agent-to-Agent (A2A) protocol.
- **Frontend**: Containerized and deployed to Google Cloud Run with `roles/aiplatform.user` service account permissions to call the deployed agent over A2A.
