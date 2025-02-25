import streamlit as st
from foamlib import FoamCase
from foamlib import FoamFile
from pathlib import Path

def initialize_state():
    """Initializes the application's global state."""
    if "case_data" not in st.session_state:
        st.session_state.case_data = {}
        case_data = st.session_state.case_data
        case_data["Case"] = None  # Initialize Case
        case_data["Case Selection"] = {}
        case_data["Case Selection"]["selected_case"] = None  # Initialize ALL values
        case_data["Case Selection"]["case_dir"] = None  # Initialize ALL values
        case_data["Mesh"] = {}
        case_data["Mesh"]["available"] = True
        case_data["Mesh"]["Paths"] = {
            "polyMesh": "constant/polyMesh",
            "cellZones": "constant/polyMesh/cellZones",
            "boundary": "constant/polyMesh/boundary"           
        }
        case_data["Mesh"]["cellZones"] = {}
        case_data["Mesh"]["boundary"] = {}
        case_data["Solver"] = {}
        case_data["Solver"]["selected"] = None  # Initialize ALL values
        case_data["Solver"]["fvSolution"] = None
        case_data["Solver"]["fvSchemes"] = None
        case_data["Solver"]["physicsProperties"] = None
        case_data["Solver"]["solidProperties"] = None
        case_data["Solver"]["poroFluidProperties"] = None
        case_data["Solver"]["poroCouplingProperties"] = None
        case_data["Solver"]["Paths"] = {
            "physicsProperties": "constant/physicsProperties",
            "solidProperties": "constant/solid/solidProperties",
            "poroFluidProperties": "constant/poroFluid/poroFluidProperties",
            "poroCouplingProperties": "constant/poroCouplingProperties"
        }
        case_data["Materials"] = {}
        case_data["Materials"]["mechanicalProperties"] = None
        case_data["Materials"]["hydraulicProperties"] = None
        case_data["Materials"]["Paths"] = {
            "mechanicalProperties": "constant/solid/mechanicalProperties",
            "poroHydraulicProperties": "constant/poroFluid/poroHydraulicProperties"
        }
        case_data["Materials"]["cell_zones_data"] = {}


#Access
def get_case():
    """Provides access to the Case Object."""
    return st.session_state.case_data.get("Case")

def get_case_data():
    """Provides access to the case_data dictionary."""
    return st.session_state.case_data

def get_path(stage: str,file: str):
    return get_case_data().get(stage).get("Paths").get(file)

def set_case(case_name):
    """Sets Case Object."""
    st.session_state.case_data["Case"] = FoamCase(Path(case_name))
        
def get_selected_case():
    return get_case_data().get("Case Selection").get("case_dir")

def get_selected_case_name():
    return get_case_data().get("Case Selection").get("selected_case")

def get_solver_type():
    return get_case_data()["Solver"].get("selected")

def has_mesh():
    return get_case_data().get("Mesh").get("available")

# Setter and for selected_case
def set_selected_case(case_name,case_dir):
    st.session_state.case_data["Case Selection"]["selected_case"] = case_name
    st.session_state.case_data["Case Selection"]["case_dir"] = case_dir

# Setter for solver_type
def set_solver_type(solver_type):
    st.session_state.case_data["Solver"]["selected"] = solver_type


