import streamlit as st
from state import *
from pathlib import Path
from foamlib import FoamFieldFile

st.title("Boundary Conditions")

st.write("Coming soon")

'''
case_dir = get_selected_case_path()
if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists(): # Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    # Get the selected solver type and its fields
    solver_type = get_solver_type()
    fields = SOLVER_OPTIONS[solver_type]["fields"]

    # Get the boundary names from the boundary file
    boundary_file = get_file("boundary")

    boundary_dict = boundary_file.as_dict()
    boundary_names = list(boundary_dict.keys())

    if not boundary_names:
        st.warning("No boundaries found in the boundary file.")
    else:
        st.success(f"Found {len(boundary_names)} boundaries: {', '.join(boundary_names)}")

        # Create tabs for each field
        field_tabs = st.tabs(fields)

        with st.form(f"boundary_conditions_{field}"):
            boundary_data = {}
            for i, field in enumerate(fields):
                with field_tabs[i]:
                    st.subheader(f"Boundary Conditions for {field}")

                    # Try to get the field file from the 0 directory
                    try:
                        field_file = FoamFieldFile(Path(get_case()) / "0" / FIELD_REGIONS[field] / field)
                        field_dict = field_file.as_dict()

                        boundary_data[field] = {}

                        # Check if boundaryField exists
                        if "boundaryField" not in field_dict:
                            st.warning(f"No boundary field found for {field}. Creating default.")
                            field_dict["boundaryField"] = {}

                        for boundary_name in boundary_names:
                            with st.expander(f"{boundary_name}"):
                                # Get the current boundary condition if it exists
                                if boundary_name in field_file.boundary_field:
                                    bc_dict = field_file.boundary_field[boundary_name].as_dict()
                                else:
                                    bc_dict = {"type": "fixedValue", "value": "uniform 0"}

                                # Allow the user to select the boundary condition type

                                bc_type = st.selectbox(
                                    "Type",
                                    options=bc_types[field],
                                    index=bc_types.index(bc_dict["type"]) if bc_dict["type"] in bc_types[field] else 0,
                                    key=f"{field}_{boundary_name}_type"
                                )

                                # If the type is fixedValue, allow the user to set the value
                                if bc_type == "fixedValue":
                                    # Check if the current value is a vector or scalar
                                    current_value = bc_dict.get("value", "uniform 0")
                                    is_vector = "(" in current_value

                                    if is_vector:
                                        # Extract the vector components
                                        try:
                                            # Parse the vector value
                                            value_str = current_value.split("uniform")[1].strip()
                                            value_str = value_str.strip("()")
                                            components = value_str.split()

                                            # Create input fields for each component
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                x = st.number_input("x", value=float(components[0]) if len(components) > 0 else 0.0, key=f"{field}_{boundary_name}_x")
                                            with col2:
                                                y = st.number_input("y", value=float(components[1]) if len(components) > 1 else 0.0, key=f"{field}_{boundary_name}_y")
                                            with col3:
                                                z = st.number_input("z", value=float(components[2]) if len(components) > 2 else 0.0, key=f"{field}_{boundary_name}_z")

                                            value = f"uniform ({x} {y} {z})"
                                        except:
                                            # If parsing fails, provide default inputs
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                x = st.number_input("x", value=0.0, key=f"{field}_{boundary_name}_x")
                                            with col2:
                                                y = st.number_input("y", value=0.0, key=f"{field}_{boundary_name}_y")
                                            with col3:
                                                z = st.number_input("z", value=0.0, key=f"{field}_{boundary_name}_z")

                                            value = f"uniform ({x} {y} {z})"
                                    else:
                                        # Extract the scalar value
                                        try:
                                            value_str = current_value.split("uniform")[1].strip()
                                            scalar_value = float(value_str)
                                            value = st.number_input("Value", value=scalar_value, key=f"{field}_{boundary_name}_value")
                                            value = f"uniform {value}"
                                        except:
                                            value = st.number_input("Value", value=0.0, key=f"{field}_{boundary_name}_value")
                                            value = f"uniform {value}"
                                else:
                                    value = None

                                # Store the boundary condition data
                                boundary_data[field][boundary_name] = {
                                    "type": bc_type
                                }
                                if value is not None:
                                    boundary_data[field][boundary_name]["value"] = value

                        # Add a submit button
                        if st.form_submit_button(f"Save {field} Boundary Conditions"):
                            for field in fields:
                                # Update the field file
                                try:
                                    with FoamFieldFile(Path(get_case()) / "0" / FIELD_REGIONS[field] / field) as field_file:
                                        for boundary_name, bc_data in boundary_data[field].items():
                                            field_file.boundary_field[boundary_name] = bc_data

                                    st.success(f"Updated boundary conditions for {field}")
                                except Exception as e:
                                    st.error(f"Error updating boundary conditions: {str(e)}")

                except Exception as e:
                    st.error(f"Error accessing field file: {str(e)}")
'''
