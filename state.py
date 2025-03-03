import streamlit as st
from foamlib import FoamCase
from foamlib import FoamFile
from pathlib import Path
import pyvista as pv

def initialize_state():
    """Initializes the application's global state."""
    if "case_data" not in st.session_state:
        st.session_state.case_data = {}
        case_data = st.session_state.case_data
        case_data["Case"] = None  # Initialize Case
        case_data["Paths"] = {
            "cellZones": "constant/polyMesh/cellZones",
            "boundary": "constant/polyMesh/boundary",
            "physicsProperties": "constant/physicsProperties",
            "solidProperties": "constant/solid/solidProperties",
            "poroFluidProperties": "constant/poroFluid/poroFluidProperties",
            "poroCouplingProperties": "constant/poroCouplingProperties",
            "mechanicalProperties": "constant/solid/mechanicalProperties",
            "poroHydraulicProperties": "constant/poroFluid/poroHydraulicProperties"
        }
        case_data["Files"] = {
                "cellZones": None,
                "boundary": None,
                "physicsProperties": None,
                "solidProperties": None,
                "poroFluidProperties": None,
                "poroCouplingProperties": None,
                "mechanicalProperties": None,
                "hydraulicProperties": None,
                "fvSolution": None,
                "fvSchemes": None,
                "controlDict": None,
                "blockMeshDict": None,
                "dotFoam": None
            }
        case_data["Case Selection"] = {
                "selected_case": None,
                "case_dir": None
        }
        case_data["Mesh"] = {
                    "cellZones": {}, # Since file format is hard to read
                    "showMeshVis": False,
                    "reader": None, # pyVista Reader
                    "internal": None, # Read with pyVista
                    "boundaries": None, # Read with pyVista
                    "df_vertices": None, # For 2D Mesh generator
                    "df_edges": None, # For 2D Mesh generator
                    "boundary": {}, # For 2D Mesh generator
                    "edgeDict": None, # For 2D Mesh generator
                    "cellSize": 0.1, # For cfMesh
                    "nBoundaryLayers": 0 # For cfMesh
        }
        case_data["Solver"] = {
                    "selected": None,  # Initialize ALL values
                    "unsaturated": False
                }
        case_data["Materials"] = {
                    "cell_zones_data": {}
                }
    if "vis" not in st.session_state:
        st.session_state.vis = {}
        vis = st.session_state.vis
        vis["show_mesh"] = True
        vis["bg_darkness"] = 0.35
        vis["selected_palette"] = 'deep'

#Access
def get_case():
    """Provides access to the Case Object."""
    return st.session_state.case_data.get("Case")

def get_case_data():
    """Provides access to the case_data dictionary."""
    return st.session_state.case_data

def get_selected_case_path():
    return get_case_data().get("Case Selection").get("case_dir")

def get_selected_case_name():
    return get_case_data().get("Case Selection").get("selected_case")

def get_solver_type():
    return get_case_data()["Solver"].get("selected")

def has_mesh():
    return Path(get_case_data()["Files"]["boundary"]).exists()

def is_unsaturated():
    return get_case_data()["Files"].poroFluidProperties["poroFluidModel"] == "varSatPoroFluid"


# Setters and for selected_case
def set_case(case_name):
    """Sets Case Object."""
    st.session_state.case_data.Case = FoamCase(Path(case_name))

def set_selected_case(case_name,case_dir):
    st.session_state.case_data["Case Selection"]["selected_case"] = case_name
    st.session_state.case_data["Case Selection"]["case_dir"] = case_dir

def set_solver_type(solver_type):
    st.session_state.case_data["Solver"]["selected"] = solver_type
