import streamlit as st
import os
import re
from tkinter.filedialog import askdirectory
import tkinter as tk
from pathlib import Path
from foamlib import FoamCase
from state import *
import shutil
from stages.solver_settings import get_solver_state_from_case

_FOAM_RUN = os.environ.get("FOAM_RUN")
if not _FOAM_RUN:
    raise RuntimeError("FOAM_RUN environment variable not set")
ROOT_DIR = Path(os.path.expanduser(_FOAM_RUN))
if not ROOT_DIR.exists():
    raise FileNotFoundError(f"FOAM_RUN directory not found: {ROOT_DIR}")

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
                        createNew(case_dir)
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
        case_data["Paths"]["dotFoam"] = case_dir/f"{get_selected_case_name()}.foam"
        dotFoam = get_file("dotFoam")
        if not dotFoam.exists():
           dotFoam.touch()
    else:
        st.info("No case directory selected yet.")



def createNew(dest: Path) -> None:
    """Create new case with template validation"""
    template_path = Path(os.environ.get("PMF_TEMPLATES", "")) / "base"
    if not template_path.exists():
        raise ValueError(f"Template directory not found: {template_path}")
        
    try:
        FoamCase(template_path).copy(dest)
    except Exception as e:
        st.error(f"Case creation failed: {str(e)}")
        raise

@st.dialog("Folder already exists!")
def agree(case_name: str, case_dir: Path) -> None:
    st.write(f"Folder {case_dir} exists!")
    st.write(f"Do you want to override and start fresh?")
    if st.button("Yes"):
        set_selected_case(case_name, case_dir)
        shutil.rmtree(case_dir)
        createNew(case_dir)
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
        load_state(directory)
        case_name = os.path.basename(os.path.normpath(directory))
        set_selected_case(case_name,Path(directory))
        st.success(f"Case directory created and saved at: {directory}")
