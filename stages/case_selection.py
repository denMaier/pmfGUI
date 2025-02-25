import streamlit as st
import os
import json
from tkinter.filedialog import askdirectory
import tkinter as tk
from pathlib import Path
from foamlib import FoamCase
from state import get_selected_case, set_selected_case, get_selected_case_name
import shutil

'''
# --- File Path for Persistent Data ---
DATA_FILE = os.path.join(os.path.expanduser("~"), ".streamlit", "app_state.json")

def load_state():
    """Loads state from JSON file, handles errors."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)  # Return the loaded data
        except Exception as e:
            st.error(f"Error loading state: {e}")
            # Consider removing a corrupted file: os.remove(DATA_FILE)
    return {}  # Return an empty dict if no file or error

def save_state(data):
    """Saves state to JSON file, handles errors."""
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)  # Ensure directory exists
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Error saving state: {e}")
        st.error("State could not be saved to disk")
'''

ROOT_DIR = os.path.join(os.path.expanduser(os.environ["FOAM_RUN"]))

def createNew():
    foamcase = FoamCase(Path(os.environ.get("PMF_TEMPLATES"))/"base").copy(get_selected_case())
    Path(get_selected_case()+f"/{get_selected_case_name()}.foam").touch()

def case_selection_stage():
    st.header("Stage 1: Case Selection")

    def browse_directory():
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        # Safely access nested dictionary keys
        initial_dir = get_selected_case()
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = ROOT_DIR  # Use .get() for environment variables too
            if not initial_dir or not os.path.exists(initial_dir):
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
            set_selected_case(case_name,directory)
            if not Path(directory+f"/{case_name}.foam").exists():
                Path(directory+f"/{case_name}.foam").touch()
            st.success(f"Case directory created and saved at: {directory}")

    method = st.radio("Choose input method:", ["New", "Browse"])

    if method == "New":
        # Safely get the default value
        default_value = get_selected_case_name()
        case_name = st.text_input("Enter OpenFOAM case directory:", value=default_value)

        if st.button("Create New Case Directory"):
            case_dir = os.path.join(ROOT_DIR,case_name)
            if not case_name:
                st.error("Please enter a directory path.")
            else:
                case_dir = os.path.join(ROOT_DIR,case_name)
                if os.path.exists(case_dir):
                    agree(case_name,case_dir)
                else:
                    try:
                        set_selected_case(case_name, case_dir)
                        createNew()
                        st.success(f"Case directory created and saved at: {case_dir}")
                    except OSError as e:
                        st.error(f"Error creating case: {e}")

    elif method == "Browse":
        if st.button("Browse"):
            browse_directory()
            

    # Display current directory (Safely access)
    case_dir = get_selected_case()
    if not case_dir:
        st.write("No case directory selected yet.")


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
