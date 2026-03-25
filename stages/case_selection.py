import os
from pathlib import Path
import shutil

from foamlib import FoamCase
import streamlit as st

from alpha_runtime import get_foam_run_path, get_foam_run_report
from state import *


def main():
    foam_run_report = get_foam_run_report()
    foam_run_path = get_foam_run_path()

    st.caption("Alpha supports creating a new case under FOAM_RUN or loading an existing case by path.")
    method = st.radio("Choose case workflow:", ["New", "Load Existing"], horizontal=True)

    if method == "New":
        create_new_case(foam_run_path, foam_run_report)
    else:
        browse_directory(foam_run_path, foam_run_report)

    if get_selected_case_path() is not None:
        case_dir = get_selected_case_path()
        dot_foam_path = case_dir / f"{get_selected_case_name()}.foam"
        PATHS["dotFoam"] = dot_foam_path
        if not dot_foam_path.exists():
            dot_foam_path.touch()
    else:
        st.info("No case directory selected yet.")


def create_new_case(foam_run_path: Path | None, foam_run_report) -> None:
    disabled = not foam_run_report.ready or foam_run_path is None
    default_value = get_selected_case_name() or ""

    if disabled:
        st.warning("New case creation is disabled until FOAM_RUN is set in the current shell.")
        issue_text = " ".join(issue.message for issue in foam_run_report.blocking_issues)
        if issue_text:
            st.caption(issue_text)

    case_name = st.text_input(
        "Case directory name inside FOAM_RUN:",
        value=default_value,
        disabled=disabled,
    )

    if foam_run_path is not None:
        st.caption(f"New cases will be created under: {foam_run_path}")

    if st.button("Create New Case", type="primary", disabled=disabled):
        if not case_name.strip():
            st.error("Please enter a case directory name.")
            return

        case_dir = foam_run_path / case_name
        if case_dir.exists():
            agree(case_name, case_dir)
            return

        try:
            createNew(case_dir)
            set_selected_case(case_name, case_dir)
            st.success(f"Created new case at: {case_dir}")
        except OSError as exc:
            st.error(f"Error creating case: {exc}")


def createNew(dest: Path) -> None:
    """Create new case with template validation"""
    template_path = Path(os.getcwd()) / "templates" / "base"
    if not template_path.exists():
        raise ValueError(f"Template directory not found: {template_path}")

    try:
        FoamCase(template_path).copy(dest)
    except Exception as exc:
        st.error(f"Case creation failed: {str(exc)}")
        raise


@st.dialog("Folder already exists!")
def agree(case_name: str, case_dir: Path) -> None:
    st.write(f"Folder {case_dir} exists!")
    st.write("Do you want to override it and start fresh?")
    if st.button("Yes"):
        shutil.rmtree(case_dir)
        createNew(case_dir)
        set_selected_case(case_name, case_dir)
        st.rerun()
    if st.button("No"):
        st.rerun()


def browse_directory(foam_run_path: Path | None, foam_run_report) -> None:
    """Provides multiple methods to select an OpenFOAM case directory."""

    initial_dir = get_selected_case_path()
    if initial_dir is None or not initial_dir.exists():
        initial_dir = foam_run_path or Path.home()

    st.subheader("Load by direct path")
    directory = st.text_input(
        "Enter the full path to your OpenFOAM case directory:",
        value=str(initial_dir),
        key="dir_path_input",
    )

    if st.button("Load From Path"):
        if os.path.isdir(directory):
            case_name = os.path.basename(os.path.normpath(directory))
            set_selected_case(case_name, Path(directory))
            load_state(directory)
            st.success(f"Loaded case from: {directory}")
        else:
            st.error(f"The path {directory} is not a valid directory")

    st.subheader("Browse FOAM_RUN")
    if foam_run_path is None or not foam_run_report.ready:
        st.info("FOAM_RUN browsing is unavailable in this shell. Load an existing case by direct path instead.")
        issue_text = " ".join(issue.message for issue in foam_run_report.blocking_issues)
        if issue_text:
            st.caption(issue_text)
        return

    try:
        available_dirs = [d for d in os.listdir(foam_run_path) if os.path.isdir(os.path.join(foam_run_path, d))]
        available_dirs.sort()

        st.caption(f"Browsing directories in: {foam_run_path}")
        case_dir = st.selectbox(
            "Select an existing case under FOAM_RUN:",
            [""] + available_dirs,
            index=0,
            key="dir_selector",
        )

        if st.button("Load Selected Case") and case_dir:
            directory = os.path.join(foam_run_path, case_dir)
            case_name = os.path.basename(os.path.normpath(directory))
            set_selected_case(case_name, Path(directory))
            load_state(directory)
            st.success(f"Loaded case from: {directory}")
    except (FileNotFoundError, PermissionError) as exc:
        st.error(f"Error accessing directory: {str(exc)}")
