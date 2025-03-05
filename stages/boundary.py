import streamlit as st
import pandas as pd  # Make sure pandas is imported in your Streamlit app
import json # for demonstration output

# Assuming your boundary condition code (with registry, classes etc.) is in a file called 'boundary_conditions.py'
from boundaryConditions.boundary import registry, get_boundary_conditions_for_field, get_parameter_details

# --- Streamlit App ---
st.title("OpenFOAM Boundary Condition Configurator")

# 1. Get List of Fields (for demonstration, hardcoding for now - in real app, you might derive this dynamically)
available_fields = ["p_rgh", "D"] # Add more fields as needed

# Dictionary to store selected boundary conditions for each field
selected_bcs = {}

st.sidebar.header("Boundary Condition Selection")

# 2. Loop through Fields and Display Selectboxes
for field_name in available_fields:
    st.sidebar.subheader(f"Field: {field_name}")
    bc_options = get_boundary_conditions_for_field(field_name)
    bc_names = list(bc_options.keys()) # Get just the names of the BCs

    if bc_names:
        selected_bc_name = st.sidebar.selectbox(
            f"Choose BC for {field_name}:",
            options=[""] + bc_names, # Add an empty option at the beginning
            index=0, # Default to empty selection
            key=f"bc_selectbox_{field_name}" # Unique key for each selectbox
        )
        selected_bcs[field_name] = selected_bc_name # Store the selected BC name
    else:
        st.sidebar.write(f"No boundary conditions available for field: {field_name}")
        selected_bcs[field_name] = "" # No BC selected

# 3. Display Selected Boundary Conditions (for review)
st.subheader("Selected Boundary Conditions:")
if any(selected_bcs.values()): # Check if any BCs are selected
    for field, bc_name in selected_bcs.items():
        if bc_name:
            st.write(f"**{field}:** {bc_name}")
        else:
            st.write(f"**{field}:** No boundary condition selected.")
else:
    st.info("No boundary conditions selected yet. Please select BCs in the sidebar.")

st.write("---")
st.write("Parameter Configuration will be implemented in the next steps.")


# Example of how you might proceed to get parameters for the selected BC (not yet integrated into UI)
if st.button("Get Parameter Details for Selected BCs (Example - Not Functional UI Yet)"):
    parameter_details_all_fields = {}
    for field_name, bc_name in selected_bcs.items():
        if bc_name:
            params = get_parameter_details(bc_name, field_name)
            if params:
                parameter_details_all_fields[field_name] = {bc_name: params}
            else:
                parameter_details_all_fields[field_name] = {bc_name: "No parameters found"}
        else:
            parameter_details_all_fields[field_name] = {"No BC Selected": {}}

    st.subheader("Parameter Details (Example Output - JSON Format):")
    st.json(parameter_details_all_fields, expanded=False)