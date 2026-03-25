# pmfGUI Alpha

`pmfGUI` is an internal alpha GUI for preparing and launching OpenFOAM-based poromechanics cases with Streamlit.

## Alpha Scope

The supported alpha workflow is:

1. Launch the app from a sourced OpenFOAM shell.
2. Create a new case under `FOAM_RUN` or load an existing case by direct path.
3. Import an existing OpenFOAM mesh, run `blockMesh`, or use the current 2D `cartesian2DMesh` path when its executable is available.
4. Edit solver, materials, physical conditions, boundary conditions, initial conditions, and run settings.
5. Launch the solver binary named by `system/controlDict` `application`.
6. Watch the live log tail and final run status in the Run page.

The alpha does not include in-app post-processing actions.

## Prerequisites

- OpenFOAM or foam-extend environment available in your shell
- `FOAM_RUN` set if you want in-app new-case creation or FOAM-root browsing
- `uv`
- Python dependencies from [`requirements.txt`](/Users/denis/Projects/pmfGUI/requirements.txt)

## First Run

Source your OpenFOAM environment first. The exact command depends on your local installation, but it should be done in the same shell you use to launch Streamlit.

```bash
source /path/to/OpenFOAM/environment
cd /Users/denis/Projects/pmfGUI
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
streamlit run Main.py
```

If `FOAM_RUN` is missing, the app still loads. Direct-path case loading stays available, while new-case creation and FOAM-root browsing are disabled with an explanation in the UI.

## Workflow Matrix

| Area | Alpha Status | Notes |
| --- | --- | --- |
| Case creation under `FOAM_RUN` | Supported | Disabled automatically when `FOAM_RUN` is missing or invalid |
| Load existing case by direct path | Supported | Works even without `FOAM_RUN` |
| OpenFOAM `polyMesh.zip` import | Supported | Extracts into `constant/polyMesh/` |
| `blockMesh` execution | Supported | Requires `blockMesh` on `PATH` |
| Current 2D `cartesian2DMesh` flow | Supported | Requires `cartesian2DMesh` on `PATH` |
| Solver/material/physical/boundary/initial/run editing | Supported | Save targets are shown in the UI |
| Solver launch from `controlDict.application` | Supported | Run metadata is persisted in `.pmf_run.json` and `.pmf_run.log` |
| Gmsh mesh generation | Experimental, disabled | Visible in the Mesh page but not executable |
| Geometry mesh workflow | Experimental, disabled | Visible in the Mesh page but not executable |
| Advanced 2D refinements | Experimental, disabled | Visible in the Mesh page but not executable |
| In-app post-processing actions | Experimental, disabled | Post Processing page is read-only in alpha |

## Runtime Files

The alpha run subsystem persists case-local runtime metadata:

- `.pmf_run.json`
- `.pmf_run.log`

The session state mirrors these values in `case_data["Run"]`:

- `status`
- `pid`
- `log_path`
- `return_code`
- `last_command`
- `started_at`

## Known Alpha Limitations

- The app is intended for internal technical users running inside a prepared OpenFOAM shell environment.
- Unsupported workflows remain visible for roadmap clarity, but their execute paths are disabled.
- Post-processing is intentionally read-only in alpha.
- Solver launch uses only the binary named in `system/controlDict` `application`. There is no GUI-side solver override or wrapper script.

## Automated Smoke Tests

Run the current smoke suite with:

```bash
./.venv/bin/python -m unittest discover -s tests
```

The smoke tests cover template parsing, case creation, cell-zone loading, `FOAM_RUN` readiness, launch command derivation, and run metadata/log rehydration.

## Alpha Ship Checklist

- OpenFOAM environment can be sourced cleanly
- `uv` environment setup works from a fresh checkout
- Supported workflow can be exercised end to end
- Unsupported workflows stay visible but clearly disabled
- App startup is graceful with and without `FOAM_RUN`
- No blocking template parse, import, or startup errors remain
