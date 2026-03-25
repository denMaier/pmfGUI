import streamlit as st
from state import get_selected_case_path, has_mesh, SOLVER_OPTIONS, FIELD_REGIONS, get_case, get_solver_type, save_state
from foamlib import FoamFieldFile
from pathlib import Path

st.title("Initial Conditions")

case_dir = get_selected_case_path()
if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists(): # Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    solver_type = get_solver_type()
    fields = SOLVER_OPTIONS[solver_type]["fields"]
    field_paths = [Path(get_case()) / "0" / FIELD_REGIONS[field] / field for field in fields]
    missing_field_paths = [path for path in field_paths if not path.exists()]

    if missing_field_paths:
        st.error("Initial-condition editing is blocked until the required field files exist:")
        st.code("\n".join(str(path) for path in missing_field_paths), language="text")
        st.stop()

    st.caption("Field save paths:")
    st.code("\n".join(str(path) for path in field_paths), language="text")

    updated_fields = {}

    with st.form("initial_conditions_form"):
        for field in fields:
            field_file = FoamFieldFile(Path(get_case()) / "0" / FIELD_REGIONS[field] / field)
            initial_field = field_file.internal_field

            if isinstance(initial_field, (int, float)):
                updated_fields[field] = st.number_input(
                    f"Initial Field for {field}",
                    value=float(initial_field),
                    key=f"initial_{field}"
                )
            else:
                vector = tuple(float(component) for component in initial_field.tolist())
                cols = st.columns(3)
                with cols[0]:
                    x = st.number_input("x", value=vector[0], key=f"initial_{field}_x")
                with cols[1]:
                    y = st.number_input("y", value=vector[1], key=f"initial_{field}_y")
                with cols[2]:
                    z = st.number_input("z", value=vector[2], key=f"initial_{field}_z")
                updated_fields[field] = (x, y, z)

        if st.form_submit_button("Save Initial Conditions"):
            for field, value in updated_fields.items():
                field_path = Path(get_case()) / "0" / FIELD_REGIONS[field] / field
                with FoamFieldFile(field_path) as field_file:
                    field_file.internal_field = value
            save_state(case_dir)
            st.success("Initial conditions saved.")
