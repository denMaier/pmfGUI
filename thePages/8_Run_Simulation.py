from pathlib import Path

import streamlit as st

from alpha_runtime import (
    get_run_preflight_report,
    start_case_run,
    stop_case_run,
    sync_run_metadata,
    tail_run_log,
)
from render_inputs import render_input_element
from state import *


def sync_session_run_state(case_dir: Path) -> dict:
    run_state = sync_run_metadata(case_dir)
    get_case_data()["Run"].update(run_state)
    return get_case_data()["Run"]


def render_run_summary(case_dir: Path, run_state: dict, report) -> None:
    st.caption(f"Run metadata: {case_dir / '.pmf_run.json'}")
    st.caption(f"Solver log: {case_dir / '.pmf_run.log'}")

    if report.details.get("application"):
        st.caption(f"Launch target from controlDict.application: {report.details['application']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Status", run_state["status"])
    col2.metric("PID", run_state["pid"] or "-")
    if run_state["return_code"] is None:
        col3.metric("Return Code", "-")
    else:
        col3.metric("Return Code", str(run_state["return_code"]))

    if run_state["started_at"]:
        st.caption(f"Started at: {run_state['started_at']}")
    if run_state["last_command"]:
        st.code(run_state["last_command"], language="bash")


@st.fragment(run_every="2s")
def render_run_panel(case_dir: Path):
    report = get_run_preflight_report(case_dir)
    run_state = sync_session_run_state(case_dir)
    is_running = run_state["status"] == "running"

    render_run_summary(case_dir, run_state, report)

    for issue in report.blocking_issues:
        st.error(issue.message)

    col1, col2 = st.columns(2)
    if col1.button(
        "Launch Solver",
        type="primary",
        disabled=(not report.ready or is_running),
        use_container_width=True,
    ):
        try:
            run_state = start_case_run(case_dir)
            get_case_data()["Run"].update(run_state)
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to launch solver: {exc}")

    if col2.button(
        "Stop Solver",
        disabled=not is_running,
        use_container_width=True,
    ):
        try:
            run_state = stop_case_run(case_dir)
            get_case_data()["Run"].update(run_state)
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to stop solver: {exc}")

    st.subheader("Live Log Tail")
    log_tail = tail_run_log(run_state.get("log_path"))
    if log_tail:
        st.code(log_tail, language="text")
    else:
        st.info("No solver log output yet.")


st.title("Run Simulation")

case_dir = get_selected_case_path()
if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists():
    st.warning("Case does not exist. Please try Case Selection again.")
else:
    tabs = st.tabs(["Settings", "Run"])
    control_dict_path = Path(case_dir) / "system" / "controlDict"

    with tabs[0]:
        st.caption(f"Save path: {control_dict_path}")
        if not control_dict_path.exists():
            st.error(f"Required file is missing: {control_dict_path}")
        else:
            control_dict_data = get_case().control_dict.as_dict()
            with st.form("control_dict_form"):
                for key, value in control_dict_data.items():
                    control_dict_data[key] = render_input_element(key, value, key_prefix="controlDict")

                if st.form_submit_button("Save Run Settings", type="primary"):
                    with get_case().control_dict as controlDict:
                        controlDict.update(control_dict_data)
                    save_state(get_selected_case_path())
                    st.success("Run settings saved.")

    with tabs[1]:
        render_run_panel(case_dir)
