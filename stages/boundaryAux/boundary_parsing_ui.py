"""
UI functions for boundary condition editing using the class-based approach.
"""
import streamlit as st
from typing import Dict, List, Tuple, Any, Optional
import re
from pathlib import Path
import numpy as np
from foamlib import FoamFieldFile

from stages.boundaryAux.boundary_database import *
from stages.boundaryAux.function1 import *

def select_boundary_condition_type(field: str, boundary_name: str, current_type: str) -> str:
    """
    Render a selection dropdown for boundary condition type.

    Args:
        field: Field name (U, p, T, etc.)
        boundary_name: Name of the boundary
        current_type: Current boundary condition type

    Returns:
        Selected boundary condition type
    """
    # Get available boundary condition types for this field
    bc_types = get_boundary_condition_types(field)

    # Initialize selection state if not exists
    selection_key = f'select_{field}_{boundary_name}'
    if f'bc_selections_{field}' not in st.session_state:
        st.session_state[f'bc_selections_{field}'] = {}

    if selection_key not in st.session_state[f'bc_selections_{field}']:
        # Use current type if valid, otherwise default to first type
        if current_type in bc_types:
            st.session_state[f'bc_selections_{field}'][selection_key] = current_type
        else:
            st.session_state[f'bc_selections_{field}'][selection_key] = bc_types[0] if bc_types else "Custom"

    # Create a selectbox for boundary condition type
    selected_bc_type = st.selectbox(
        "Boundary Condition Type",
        options=bc_types,
        index=bc_types.index(st.session_state[f'bc_selections_{field}'][selection_key]) if st.session_state[f'bc_selections_{field}'][selection_key] in bc_types else 0,
        key=selection_key
    )

    return selected_bc_type

def generate_boundary_condition(field: str, boundary_name: str, bc_type: str, default_dict: Dict[str, Any]) -> BoundaryCondition:
    """
    Render editor for a boundary condition.

    Args:
        field: Field name (U, p, T, etc.)
        boundary_name: Name of the boundary
        bc_type: Boundary condition type
        default_dict: Default boundary condition dictionary

    Returns:
        Updated BoundaryCondition object
    """
    if bc_type == "Custom":
        # For custom type, show a text area with the raw dictionary
        st.info("Enter custom boundary condition in OpenFOAM syntax")

        # Convert dictionary to string for editing
        default_str = "\n".join([f"{k} {v};" for k, v in default_dict.items()])

        custom_text = st.text_area(
            "Custom Boundary Condition",
            value=default_str,
            height=200,
            key=f"{field}_{boundary_name}_custom"
        )

        # Parse the custom text back to a dictionary
        custom_dict = {}
        custom_dict["type"] = default_dict.get("type", "fixedValue")

        for line in custom_text.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            if ";" in line:
                line = line.rstrip(";")

            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                key, value = parts
                custom_dict[key.strip()] = value.strip()

        # Create a boundary condition from the dictionary
        return BoundaryCondition.from_dict(custom_dict)
    else:
        # Get template for this field and boundary condition type
        template = get_boundary_condition_template(field, bc_type)

        # Create a boundary condition from the default dictionary
        bc = BoundaryCondition.from_dict(default_dict)

        # If the types don't match, use the template but preserve values where possible
        if bc.type != bc_type:
            # Create a new boundary condition from template
            bc = template
            bc.type = bc_type

        return bc

def preselect_function1_types(field: str, boundary_name: str, bc: BoundaryCondition) -> None:
    """
    Pre-select Function1 types for a boundary condition outside the form.

    Args:
        field: Field name (U, p, T, etc.)
        boundary_name: Name of the boundary
        bc: BoundaryCondition object to examine
    """
    # Initialize session state for Function1 selections if needed
    if 'function1_selections' not in st.session_state:
        st.session_state['function1_selections'] = {}

    # Find all Function1 fields in this boundary condition
    for field_key, field_value in bc.entries.items():
        if isinstance(field_value, Function1):
            f1_key = f"{field}_{boundary_name}_{field_key}_f1_type"

            # Initialize with detected type if not already set
            if f1_key not in st.session_state['function1_selections']:
                current_type = Function1Registry.detect_type(field_value)
                st.session_state['function1_selections'][f1_key] = current_type

            # Create the Function1 type selector
            function1_options = Function1Registry.get_type_options()
            selected_type = st.selectbox(
                f"{field_key} Type",
                options=[t[0] for t in function1_options],
                format_func=lambda x: next((t[1] for t in function1_options if t[0] == x), x),
                index=[t[0] for t in function1_options].index(st.session_state['function1_selections'][f1_key])
                    if st.session_state['function1_selections'][f1_key] in [t[0] for t in function1_options] else 0,
                key=f1_key
            )

            # Update the session state with the selected type
            st.session_state['function1_selections'][f1_key] = selected_type

def save_boundary_condition(field: str, boundary_name: str, bc: BoundaryCondition, foam_file_path: Path) -> Tuple[bool, str]:
    """
    Save a boundary condition to the OpenFOAM field file.

    Args:
        field: Field name (U, p, T, etc.)
        boundary_name: Name of the boundary
        bc: BoundaryCondition object
        foam_file_path: Path to the OpenFOAM field file

    Returns:
        Success status and message
    """
    try:
        # Convert BoundaryCondition to dictionary
        bc_dict = {"type": bc.type}
        for key, value in bc.entries.items():
            if hasattr(value, 'to_foam'):
                # Function1 or other object with to_foam method
                bc_dict[key] = value.to_foam()
            else:
                # Regular value
                bc_dict[key] = value

        # Open the field file and update the boundary
        with FoamFieldFile(foam_file_path) as field_file:
            field_file.boundary_field[boundary_name] = bc_dict

        return True, f"Updated boundary condition for {boundary_name}"
    except Exception as e:
        return False, f"Error updating boundary condition: {str(e)}"
