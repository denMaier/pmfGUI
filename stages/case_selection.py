import streamlit as st
import os
from tkinter.filedialog import askdirectory
import tkinter as tk
from pathlib import Path
from foamlib import FoamCase
from state import *
import shutil
from stages.solver_settings import get_solver_state_from_case
from stages.mesh import load_case_cell_zones

ROOT_DIR = os.path.join(os.path.expanduser(os.environ["FOAM_RUN"]))

def load_state(case_dir):
    case_data = st.session_state.case_data
    case_data["Case"] = FoamCase(case_dir)
    for file, path in case_data["Paths"].items():
        case_data["Files"][file] = case_data["Case"].file(Path(case_dir)/path)
    case_data["Files"]["fvSolution"] = case_data["Case"].fv_solution
    case_data["Files"]["fvSchemes"] = case_data["Case"].fv_schemes
    case_data["Files"]["controlDict"] = case_data["Case"].control_dict
    case_data["Files"]["blockMeshDict"] = case_data["Case"].block_mesh_dict
    get_solver_state_from_case(case_dir)
    if Path(case_data["Files"]["boundary"]).exists() and Path(case_data["Files"]["cellZones"]).exists():
        load_case_cell_zones(case_dir)

def main():
    method = st.radio("Choose input method:", ["New", "Browse"])

    if method == "New":
        # Safely get the default value
        default_value = get_selected_case_name()
        case_name = st.text_input("Enter OpenFOAM case directory:", value=default_value)

        if st.button("Create New Case Directory"):
            if case_name is None:
                st.error("Please enter a directory path.")
            else:
                case_dir = Path(ROOT_DIR)/case_name
                if case_dir.exists():
                    agree(case_name,case_dir)
                else:
                    try:
                        createNew()
                        set_selected_case(case_name, case_dir)
                        st.success(f"Case directory created and saved at: {case_dir}")
                    except OSError as e:
                        st.error(f"Error creating case: {e}")

    elif method == "Browse":
        if st.button("Browse"):
            browse_directory()

    if get_selected_case_path() is not None:
        case_dir = get_selected_case_path()
        case_data = get_case_data()
        load_state(case_dir)
        case_data["Files"]["dotFoam"] = case_dir/f"{get_selected_case_name()}.foam"
        if not case_data["Files"]["dotFoam"].exists():
            case_data["Files"]["dotFoam"].touch()
    else:
        st.write("No case directory selected yet.")



def createNew():
    FoamCase(Path(os.environ.get("PMF_TEMPLATES"))/"base").copy(get_selected_case_path())

@st.dialog("Folder already exists!")
def agree(case_name,case_dir):
    st.write(f"Folder {case_dir} exists!")
    st.write(f"Do you want to override and start fresh?")
    if st.button("Yes"):
        set_selected_case(case_name, case_dir)
        shutil.rmtree(case_dir)
        createNew()
        st.rerun()
    if st.button("No"):
        st.rerun()

def browse_directory():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    # Safely access nested dictionary keys
    initial_dir = get_selected_case_path()
    if initial_dir is not None:
        if not initial_dir.exists():
            initial_dir = Path(ROOT_DIR)
            if not initial_dir.exists():
                initial_dir = os.getcwd()
    else:
        initial_dir = Path(ROOT_DIR)
        if not initial_dir.exists():
            initial_dir = os.getcwd()
    try:
        directory = askdirectory(title="Select OpenFOAM case directory", initialdir=initial_dir)
    except tk.TclError:
        st.error("Tkinter error. Ensure Tkinter is installed correctly.")
        return

    root.attributes('-topmost', False)
    root.destroy()

    if directory:
        case_name = os.path.basename(os.path.normpath(directory))
        set_selected_case(case_name,Path(directory))
        st.success(f"Case directory created and saved at: {directory}")
