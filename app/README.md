# DynNav Interactive Robotics Lab

The Streamlit application is an interactive research-software environment for exploring deterministic synthetic navigation, occupancy belief, uncertainty, risk-sensitive planning, dynamic obstacles, multi-robot coordination concepts, and the C01–C26 contribution demonstrations.

> Synthetic interactive research environment. Results shown here do not establish physical-robot safety, ROS2 validation, Gazebo execution, deployment readiness, certified autonomy, or formal guarantees.

## Install

```bash
python -m pip install -e ".[dashboard,dev]"
```

## Run locally

```bash
streamlit run app/dashboard.py
```

Headless startup:

```bash
streamlit run app/dashboard.py \
  --server.headless true \
  --server.address 0.0.0.0 \
  --server.port 8501
```

## Run with Docker

Build the dedicated dashboard image from the repository root:

```bash
docker build -t dynnav-streamlit .
```

Run the application:

```bash
docker run --rm -p 8501:8501 dynnav-streamlit
```

Open `http://localhost:8501`. The image runs as a non-root user and exposes a Streamlit health check at `/_stcore/health`.

To make generated result files visible on the host, mount the results directory:

```bash
mkdir -p results
docker run --rm -p 8501:8501 \
  -v "$(pwd)/results:/workspace/results" \
  dynnav-streamlit
```

The Docker image contains the synthetic Streamlit laboratory only. It does not install or validate ROS2, Nav2, Gazebo, GPU drivers, or robot hardware interfaces.

## Page map

| Page | Purpose |
|---|---|
| Home | Entry points, capability summary, and research boundary |
| Robot Lab | Closed-loop playback, event inspection, and exports |
| Scenario Builder | Configure and export deterministic scenarios |
| Planner Arena | Compare Classical A* and Risk-aware A* on the same world |
| Belief & Mapping Lab | Inspect prior/posterior occupancy belief and uncertainty |
| Risk & Safety Lab | Compose risk layers and test supervisor thresholds |
| Dynamic Obstacles | Explore motion models, prediction, and route conflicts |
| Multi-Robot Lab | Explore synthetic fleet communication and conflicts |
| Contribution Explorer | Search and run C01–C26 interactive renderers |
| Experiment Studio | Run single, multi-seed, comparison, and sweep experiments |
| Results & Reports | Upload, filter, replay, compare, and export manifests |
| Documentation | Browse curated repository Markdown safely |
| System Status | Inspect runtime, dependencies, and available capabilities |

## Contribution registry

Contribution metadata is defined in:

```text
src/dynnav_dashboard/contribution_registry.yaml
```

Renderers are registered in:

```text
src/dynnav_dashboard/contributions/__init__.py
```

Each contribution retains its own controls, plots, metrics, interpretation, and maturity information. Contributions are synthetic research demonstrations and are not assumed to have equal validation maturity.

## Determinism and session state

The simulation utilities use explicit random seeds. Pages preserve active scenarios, runs, filters, playback frames, and generated experiment records in Streamlit session state. Changing unrelated presentation controls should not silently replace the active run.

## Exports

Depending on the page, the app can export:

- scenario YAML and JSON;
- planner-comparison CSV;
- event logs;
- experiment manifests;
- result CSV and JSON;
- Markdown reports;
- ZIP run bundles.

Browser downloads are generated from the current deterministic session. Persistent server-side storage is not guaranteed on Streamlit Community Cloud.

## Validation and tests

Run the integrity validator:

```bash
python scripts/validate_streamlit_app.py
```

Run the dashboard smoke tests:

```bash
pytest tests/test_streamlit_lab_smoke.py
```

Run the complete test suite:

```bash
pytest
```

Run formatting and lint checks:

```bash
ruff check .
black --check .
```

The smoke tests parse every Streamlit page, verify the C01–C26 registry/renderer contract, inspect the Docker entry point, and check that responsible evidence notices remain visible.

## Deployment notes

Entry point:

```text
app/dashboard.py
```

The dashboard requires Python 3.10+ and the `dashboard` optional dependency group. No secret is required for the synthetic simulations. Copy `.streamlit/secrets.toml.example` only when adding optional external integrations, and never commit real credentials.

Community-hosted deployments may provide ephemeral filesystems. Use browser downloads for experiment persistence, and do not assume data written to `results/` survives a restart.

## Troubleshooting

**Module import failure**

```bash
python -m pip install -e ".[dashboard]"
```

**A page does not appear**

Verify its file exists under `app/pages/` and run:

```bash
python scripts/validate_streamlit_app.py
```

**Docker health check fails**

Inspect the container logs:

```bash
docker logs <container-name-or-id>
```

Confirm port `8501` is free and that the application was built from the current repository root.

**Slow contribution renderer**

Reduce grid sizes, episode counts, or sweep ranges. Contribution renderers are loaded only when selected, but expensive numerical controls still increase runtime.

**ROS2 or Gazebo unavailable**

The Streamlit app does not require or claim ROS2/Gazebo execution. Those capabilities must be validated separately in a suitable robotics environment.
