import streamlit as st
from foamlib import FoamCase, FoamFile
from pathlib import Path
import json
import re
from alpha_runtime import default_run_state, load_cell_zones
from app_core import (
    BC_TYPES,
    FIELD_DEFAULT_VALUE,
    FIELD_REGIONS,
    PATHS,
    POROFLUIDMODEL_TYPES,
    SOLVER_OPTIONS,
    SOLVER_TYPE_MAP,
)

def initialize_state():
    """Initializes the application's global state."""
    if "case_data" not in st.session_state:
        st.session_state.case_data = {}

    case_data = st.session_state.case_data
    case_data.setdefault("Case", None)
    case_data.setdefault("Case Selection", {"selected_case": None})
    case_data.setdefault(
        "Mesh",
        {
            "cellZones": {},
            "showMeshVis": False,
            "df_vertices": None,
            "df_edges": None,
            "edgeDict": {},
            "cellSize": 0.1,
            "nBoundaryLayers": 0,
        },
    )
    case_data.setdefault(
        "Solver",
        {
            "selected": None,
            "unsaturated": None,
        },
    )
    case_data.setdefault("Run", default_run_state())
    if "vis" not in st.session_state:
        st.session_state.vis = {}
        vis = st.session_state.vis
        vis["show_mesh"] = True
        vis["bg_darkness"] = 0.35
        vis["selected_palette"] = 'deep'
        vis["style"] = 'surface'
        vis["color_patches"] = False
        vis["show_boundaries"] = True
        vis["only_boundaries"] = True
        vis["opacity"] = 1.0
        vis['available_regions'] = ['solid', 'poroFluid']
#Access
def get_case():
    """Provides access to the Case Object."""
    return st.session_state.case_data.get("Case")

def get_case_data():
    """Provides access to the case_data dictionary."""
    return st.session_state.case_data

def get_selected_case_path():
    case = st.session_state.case_data.get("Case")
    if case is not None:
        return Path(case)
    else:
        return case

def get_selected_case_name():
    return get_case_data().get("Case Selection").get("selected_case")

def get_solver_type():
    selected = get_case_data()["Solver"].get("selected")
    if selected is None:
        physicsProperties = get_file("physicsProperties")
        selected = SOLVER_TYPE_MAP[physicsProperties["type"]]
    return selected

def is_unsaturated():
    solver = get_solver_type()
    if solver in ["Coupled","Groundwater"]:
        poroFluidProperties = get_file("poroFluidProperties")
        if st.session_state.case_data["Solver"].get("unsaturated") is None and poroFluidProperties is not None:
            unsat = (poroFluidProperties["poroFluidModel"] == "varSatPoroFluid")
            st.session_state.case_data["Solver"]["unsaturated"] = unsat
            return unsat
        else:
            return st.session_state.case_data["Solver"].get("unsaturated")
    return False

def has_mesh():
    return (Path(get_case()) / PATHS["boundary"]).exists()

def get_cell_zones():
    cellZones = st.session_state.case_data["Mesh"].get("cellZones")
    if not cellZones and has_mesh():
        load_case_cell_zones()
    return st.session_state.case_data["Mesh"].get("cellZones")

def get_file(filename: str) -> FoamFile:
    """
    Retrieves a FoamFile object for the specified filename from the active case.

    Args:
        filename: Key from the Paths configuration to lookup the file path

    Returns:
        FoamFile object if valid configuration and file exists, None otherwise

    Raises:
        ValueError: If filename is not found in Paths configuration
        RuntimeError: If no active case is configured
    """
    case = get_case()
    if not case:
        raise RuntimeError("No active Foam case configured")

    path_config = PATHS.get(filename)
    if not path_config:
        raise ValueError(f"Path configuration missing for '{filename}'")

    filepath = Path(get_case())/path_config
    if not filepath.exists():
        st.error(f"File not found: {filepath}")
        st.stop()

    try:
        return case.file(filepath)
    except Exception as e:
        st.error(f"Error accessing {filename}: {str(e)}")
        st.stop()

# Setters and for selected_case

def set_selected_case(case_name,case_dir):
    st.session_state.case_data["Case Selection"]["selected_case"] = case_name
    st.session_state.case_data["Case"] = FoamCase(Path(case_dir))
    st.session_state.case_data["Mesh"]["cellZones"] = {}
    st.session_state.case_data["Mesh"]["showMeshVis"] = False
    st.session_state.case_data["Solver"]["selected"] = None
    st.session_state.case_data["Solver"]["unsaturated"] = None
    st.session_state.case_data["Run"] = default_run_state()

def set_solver_type(solver_type):
    st.session_state.case_data["Solver"]["selected"] = solver_type
    st.session_state.case_data["Solver"]["unsaturated"] = None
    physicsProperties = get_file("physicsProperties")
    if physicsProperties is not None:
        with physicsProperties:
            physicsProperties["type"] = SOLVER_OPTIONS[solver_type]["type"]

def load_state(case_dir: Path) -> None:
    """Loads state from a file within the case directory, if available."""
    state_file_path = Path(case_dir) / ".pmf_state.json"
    if not state_file_path.exists():
        st.info("No saved state file found. Starting with default state.")
        return

    try:
        with open(state_file_path, "r") as f:
            loaded_state = json.load(f)

        # Merge loaded state into current session state, avoid overwriting 'Case'
        case_data = st.session_state.case_data
        for key, value in loaded_state.items():
            if key not in {"Case", "Run"}: # Run state is stored separately
                case_data[key] = value
        st.success(f"Loaded state from: {state_file_path}")
    except FileNotFoundError:
        st.warning(f"No state file found at: {state_file_path}")
    except json.JSONDecodeError:
        st.error(f"Error decoding state file {state_file_path}. File may be corrupted.")
    except Exception as e:
        st.error(f"Error loading state from {state_file_path}: {str(e)}")

def clear_state(case_dir: Path) -> None:
    """Clears the state for a given case directory."""
    if "case_data" in st.session_state:
        case_name = st.session_state.case_data["Case Selection"]["selected_case"]
        st.session_state.case_data = {} # Reset case_data
        initialize_state() # Re-initialize to default
        st.session_state.case_data["Case"] = FoamCase(case_dir)
        st.session_state.case_data["Case Selection"]["selected_case"] = case_name
        st.success(f"Cleared state for case: {case_dir}")
    else:
        st.warning("No state to clear.")

def clear_stage_state(stage: str) -> None:
    """Clears the state for a given stage."""
    if stage in st.session_state.case_data:
        st.session_state.case_data[stage] = {} # Reset case_data
        st.success(f"Cleared state for stage: {stage}")
    else:
        st.warning("No state to clear.")

def save_state(case_dir: Path) -> None:
    """Saves the current state to a file within the case directory."""
    state_file_path = Path(case_dir) / ".pmf_state.json"

    # Extract state to save (exclude FoamCase and file_mtimes)
    state_to_save = {
        key: value for key, value in st.session_state.case_data.items()
        if key not in ["Case", "Run", "file_mtimes"]
    }

    try:
        with open(str(state_file_path), "w") as f:
            json.dump(state_to_save, f, indent=4)
        st.success(f"Saved state to: {state_file_path}")
    except Exception as e:
        st.error(f"Error saving state: {str(e)}")

def load_case_cell_zones():
    """
    Extracts cellZone names from an OpenFOAM cellZones file,
    handling variations in whitespace, line breaks, and the FoamFile header.

    Args:

    Returns:
        list: A list of cellZone names (strings). Returns an empty list if no
              cellZones are found or if an error occurs.
    """

    case_path = get_selected_case_path()
    if case_path is None:
        st.warning("No case selected. Please select a case first.")
        return

    filePath = case_path / PATHS["cellZones"]
    get_case_data()["Mesh"]["cellZones"] = {}

    if not filePath.exists():
        st.warning("No CellZones exist! Please create at least one cellZone!")
        return

    try:
        get_case_data()["Mesh"]["cellZones"] = load_cell_zones(case_path)
        if not get_case_data()["Mesh"]["cellZones"]:
            st.error("No cellZones in cellZone file found!!")
    except FileNotFoundError:
        print(f"Error: File not found at {filePath}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
