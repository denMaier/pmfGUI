"""
Classes for representing OpenFOAM boundary conditions in a structured way.
"""
from typing import Dict, List, Union, Optional, Any
from dataclasses import dataclass, field
import numpy as np
import streamlit as st
from stages.boundary.function1 import Function1, Function1Registry
from boundaryConditions.boundary_templates import BOUNDARY_CONDITION_TEMPLATES


@dataclass
class BoundaryCondition:
    """Base class for all boundary conditions."""
    name: str = ""
    type: str = ""
    entries: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_foam(self) -> str:
        """Convert to OpenFOAM syntax string."""
        lines = [f"type {self.type};"]

        for key, value in self.entries.items():
            if isinstance(value, Function1):
                # Handle Function1 entries
                lines.append(f"{key} {value.to_foam()};")
            elif isinstance(value, (list, np.ndarray)) and len(value) == 3:
                # Handle vector values
                lines.append(f"{key} ({value[0]} {value[1]} {value[2]});")
            elif isinstance(value, bool):
                # Handle boolean values
                lines.append(f"{key} {str(value).lower()};")
            else:
                # Handle other values
                lines.append(f"{key} {value};")

        return "\n".join(lines)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoundaryCondition':
        """Create a BoundaryCondition from a dictionary."""
        bc = cls()
        bc.type = data.get("type", "")

        # Map field keys and values
        for key, value in data.items():
            if key == "type":
                continue

            # Handle Function1 strings
            if isinstance(value, str) and ("uniform" in value or any(ft in value for ft in Function1Registry.get_all_types())):
                bc.entries[key] = Function1.from_foam(value, selectable = True)
            else:
                bc.entries[key] = value

        return bc

    def render_ui(self, entry: str, boundary_name: str) -> 'BoundaryCondition':
        """Render UI for this boundary condition and return updated instance."""
        st.subheader(f"{self.type} Boundary Condition")

        if self.description:
            st.info(self.description)

        updated_entries = {}

        for entry_key, entry_value in self.entries.items():
            if isinstance(entry_value, Function1):
                updated_entries[entry_key] = entry_value.render_ui(
                    entry_key,
                    f"{field}_{boundary_name}_{entry_key}")  # Skip selector if using from session
            elif isinstance(entry_value, (list, np.ndarray)) and len(entry_value) == 3:
                # Render vector entries
                cols = st.columns(3)
                with cols[0]:
                    x = st.number_input(f"{entry_key} X", value=float(entry_value[0]),
                                       key=f"{entry}_{boundary_name}_{entry_key}_x")
                with cols[1]:
                    y = st.number_input(f"{entry_key} Y", value=float(entry_value[1]),
                                       key=f"{entry}_{boundary_name}_{entry_key}_y")
                with cols[2]:
                    z = st.number_input(f"{entry_key} Z", value=float(entry_value[2]),
                                       key=f"{entry}_{boundary_name}_{entry_key}_z")
                updated_entries[entry_key] = [x, y, z]
            elif isinstance(entry_value, bool):
                # Render boolean entries
                updated_entries[entry_key] = st.checkbox(
                    entry_key,
                    value=entry_value,
                    key=f"{entry}_{boundary_name}_{entry_key}"
                )
            elif isinstance(entry_value, (int, float)):
                # Render numeric entries
                updated_entries[entry_key] = st.number_input(
                    entry_key,
                    value=float(entry_value),
                    key=f"{entry}_{boundary_name}_{entry_key}"
                )
            elif isinstance(entry_value, str):
                # Check if it's a selection entry
                if entry_key == "effectiveStressModel":
                    options = ["suctionCutOff", "terzaghi", "niemunis", "bishop"]
                    updated_entries[entry_key] = st.selectbox(
                        entry_key,
                        options=options,
                        index=options.index(entry_value) if entry_value in options else 0,
                        key=f"{entry}_{boundary_name}_{entry_key}"
                    )
                elif "uniform" in entry_value or any(f1_type in entry_value for f1_type in ["tableFile", "csvFile", "ramp", "cosine"]):
                    # This looks like a Function1 string - parse and render
                    f1 = Function1.from_foam(entry_value)
                    updated_entries[entry_key] = f1.render_ui(
                        entry_key,
                        f"{entry}_{boundary_name}_{entry_key}"
                    )
                else:
                    # Render text entries
                    updated_entries[entry_key] = st.text_input(
                        entry_key,
                        value=entry_value,
                        key=f"{entry}_{boundary_name}_{entry_key}"
                    )
            else:
                # For unhandled types, just keep the original value
                updated_entries[entry_key] = entry_value

        # Create a new instance with updated entries
        updated_bc = BoundaryCondition(
            name=self.name,
            type=self.type,
            entries=updated_entries,
            description=self.description
        )

        return updated_bc

def get_boundary_condition_template(field: str, bc_type: str) -> BoundaryCondition:
    """Get a boundary condition template for a field and type."""
    # Try to get the template for the specific field
    field_templates = BOUNDARY_CONDITION_TEMPLATES.get(field, {})

    # If found, return the specified type or default to fixedValue
    if field_templates:
        return field_templates.get(bc_type, field_templates["fixedValue"])

    # If no template found, create a basic one
    return BoundaryCondition(type=bc_type, description=f"{bc_type} boundary condition")

def get_boundary_condition_types(field: str) -> List[str]:
    """Get available boundary condition types for a field."""
    field_templates = BOUNDARY_CONDITION_TEMPLATES.get(field, {})
    return list(field_templates.keys())
