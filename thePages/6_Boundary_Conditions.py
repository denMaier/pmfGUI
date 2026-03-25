import streamlit as st
from pathlib import Path

from stages.boundary.boundary import main
from state import FIELD_REGIONS, SOLVER_OPTIONS, get_selected_case_path, get_solver_type, has_mesh

st.title("Boundary Conditions")

case_dir = get_selected_case_path()
if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists():  # Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    physics_path = case_dir / "constant/physicsProperties"
    boundary_path = case_dir / "constant/polyMesh/boundary"
    missing_paths = []
    if not physics_path.exists():
        missing_paths.append(physics_path)
    if not boundary_path.exists():
        missing_paths.append(boundary_path)

    if missing_paths:
        st.error("This case is missing required boundary-condition files:")
        st.code("\n".join(str(path) for path in missing_paths), language="text")
    else:
        solver_type = get_solver_type()
        field_paths = [
            Path(case_dir) / "0" / FIELD_REGIONS[field_name] / field_name
            for field_name in SOLVER_OPTIONS[solver_type]["fields"]
        ]
        missing_field_paths = [path for path in field_paths if not path.exists()]

        if missing_field_paths:
            st.error("Boundary editing is blocked until the required field files exist:")
            st.code("\n".join(str(path) for path in missing_field_paths), language="text")
        else:
            st.caption(f"Boundary mesh path: {boundary_path}")
            st.caption("Field save paths:")
            st.code("\n".join(str(path) for path in field_paths), language="text")
            main()
