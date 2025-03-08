import streamlit as st
from state import *
from stages.boundaryNew import *

st.title("Boundary Conditions")

st.write("This page is under construction.")

case_dir = get_selected_case_path()
if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists():  # Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    # Get the selected solver type and its fields
    main()


                # except Exception as e:
                #     st.error(f"Error accessing field file: {str(e)}")


                #                 if boundary_name in field_file.boundary_field:
                #                     bc_dict = field_file.boundary_field[boundary_name].as_dict()
                #                 else:
                #                     bc_dict = {"type": "fixedValue", "value": "uniform 0"}

                #                 # Allow the user to select the boundary condition type

                #                 bc_type = st.selectbox(
                #                     "Type",
                #                     options=bc_types[field],
                #                     index=bc_types.index(bc_dict["type"]) if bc_dict["type"] in bc_types[field] else 0,
                #                     key=f"{field}_{boundary_name}_type"
                #                 )

                #                 # If the type is fixedValue, allow the user to set the value
                #                 if bc_type == "fixedValue":
                #                     # Check if the current value is a vector or scalar
                #                     current_value = bc_dict.get("value", "uniform 0")
                #                     is_vector = "(" in current_value

                #                     if is_vector:
                #                         # Extract the vector components
                #                         try:
                #                             # Parse the vector value
                #                             value_str = current_value.split("uniform")[1].strip()
                #                             value_str = value_str.strip("()")
                #                             components = value_str.split()

                #                             # Create input fields for each component
                #                             col1, col2, col3 = st.columns(3)
                #                             with col1:
                #                                 x = st.number_input("x", value=float(components[0]) if len(components) > 0 else 0.0, key=f"{field}_{boundary_name}_x")
                #                             with col2:
                #                                 y = st.number_input("y", value=float(components[1]) if len(components) > 1 else 0.0, key=f"{field}_{boundary_name}_y")
                #                             with col3:
                #                                 z = st.number_input("z", value=float(components[2]) if len(components) > 2 else 0.0, key=f"{field}_{boundary_name}_z")

                #                             value = f"uniform ({x} {y} {z})"
                #                         except:
                #                             # If parsing fails, provide default inputs
                #                             col1, col2, col3 = st.columns(3)
                #                             with col1:
                #                                 x = st.number_input("x", value=0.0, key=f"{field}_{boundary_name}_x")
                #                             with col2:
                #                                 y = st.number_input("y", value=0.0, key=f"{field}_{boundary_name}_y")
                #                             with col3:
                #                                 z = st.number_input("z", value=0.0, key=f"{field}_{boundary_name}_z")

                #                             value = f"uniform ({x} {y} {z})"
                #                     else:
                #                         # Extract the scalar value
                #                         try:
                #                             value_str = current_value.split("uniform")[1].strip()
                #                             scalar_value = float(value_str)
                #                             value = st.number_input("Value", value=scalar_value, key=f"{field}_{boundary_name}_value")
                #                             value = f"uniform {value}"
                #                         except:
                #                             value = st.number_input("Value", value=0.0, key=f"{field}_{boundary_name}_value")
                #                             value = f"uniform {value}"
                #                 else:
                #                     value = None

                #                 # Store the boundary condition data
                #                 boundary_data[field][boundary_name] = {
                #                     "type": bc_type
                #                 }
                #                 if value is not None:
                #                     boundary_data[field][boundary_name]["value"] = value
