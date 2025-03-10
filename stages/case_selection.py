import streamlit as st
import os
import re
from tkinter.filedialog import askdirectory
import tkinter as tk
from pathlib import Path
from foamlib import FoamCase
from state import *
import shutil

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
        browse_directory()

    if get_selected_case_path() is not None:
        case_dir = get_selected_case_path()
        case_data = get_case_data()
        PATHS["dotFoam"] = case_dir/f"{get_selected_case_name()}.foam"
        if not Path(PATHS["dotFoam"]).exists():
           Path(PATHS["dotFoam"]).touch()
    else:
        st.info("No case directory selected yet.")



def createNew(dest: Path) -> None:
    """Create new case with template validation"""
    template_path = Path(os.getcwd()) / "templates" / "base"
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
    """Provides multiple methods to select an OpenFOAM case directory."""

    # Get default value and available directories
    initial_dir = get_selected_case_path()
    if initial_dir is None or not initial_dir.exists():
        initial_dir = Path(ROOT_DIR)

    # Option 1: Direct path input
    st.write("### Enter Directory Path")
    directory = st.text_input(
        "Enter the full path to your OpenFOAM case directory:",
        value=str(initial_dir),
        key="dir_path_input"
    )

    if st.button("Load From Path"):
        if os.path.isdir(directory):
            load_state(directory)
            case_name = os.path.basename(os.path.normpath(directory))
            set_selected_case(case_name, Path(directory))
            st.success(f"Case directory created and saved at: {directory}")
        else:
            st.error(f"The path {directory} is not a valid directory")

    # Option 2: Browse from ROOT_DIR
    st.write("### Select from existing directories")

    # Optional: Allow to set a custom search directory
    search_dir = st.text_input(
        "Search directory (leave empty for default):",
        value="",
        key="search_dir_input"
    )

    # Use either the custom search dir or the ROOT_DIR
    browse_root = search_dir if search_dir and os.path.isdir(search_dir) else ROOT_DIR

    # Find directories in the browse_root
    try:
        available_dirs = [d for d in os.listdir(browse_root)
                         if os.path.isdir(os.path.join(browse_root, d))]
        available_dirs.sort()

        # Display the current search directory
        st.info(f"Browsing directories in: {browse_root}")

        # Create a selectbox for choosing a directory
        case_dir = st.selectbox(
            "Select an existing case:",
            [""] + available_dirs,
            index=0,
            key="dir_selector"
        )

        if st.button("Load Selected Case") and case_dir:
            directory = os.path.join(browse_root, case_dir)
            load_state(directory)
            case_name = os.path.basename(os.path.normpath(directory))
            set_selected_case(case_name, Path(directory))
            st.success(f"Case directory created and saved at: {directory}")
    except (FileNotFoundError, PermissionError) as e:
        st.error(f"Error accessing directory: {str(e)}")
