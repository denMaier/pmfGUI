from pathlib import Path
from foamlib import FoamFieldFile
from state import *
from stages.boundaryAux.boundary_database import *
from stages.boundaryAux.boundary_parsing_ui import *

@st.fragment
def main():
    """Fragment containing boundary conditions UI"""
    solver_type = get_solver_type()
    fields = SOLVER_OPTIONS[solver_type]["fields"]

    # Get the boundary names from the boundary file
    boundary_file = get_file("boundary")

    boundaries = boundary_file.as_dict()[None]
    patch_boundaries = []
    empty_boundaries = []
    symmetry_boundaries = []
    cyclic_boundaries = []
    none_boundaries = []
    for boundary in boundaries:
        boundary_name, boundaryTypeDict = boundary
        if boundaryTypeDict["type"] == "patch":
            patch_boundaries.append(boundary_name)
        elif boundaryTypeDict["type"] == "empty":
            empty_boundaries.append(boundary_name)
        elif boundaryTypeDict["type"] == "symmetry":
            symmetry_boundaries.append(boundary_name)
        elif boundaryTypeDict["type"] == "cyclic":
            cyclic_boundaries.append(boundary_name)
        else:
            none_boundaries.append(boundary_name)

    if len(none_boundaries) > 0:
        st.warning(
            f"Found {len(none_boundaries)} boundaries with no valid type specified.\n {none_boundaries}"
        )

    if not patch_boundaries:
        st.warning("No patch boundaries found in the boundary file.")
    else:
        st.success(f"Found {len(patch_boundaries)} patch boundaries")

        # Create tabs for each field
        field_tabs = st.tabs(fields)

        # Within your field_tabs loop:
        for i, field in enumerate(fields):
            with field_tabs[i]:
                # Try to get the field file from the 0 directory
                field_file_path = Path(get_case()) / "0" / FIELD_REGIONS[field] / field
                field_file = FoamFieldFile(field_file_path)
                field_boundary_dict = field_file.boundary_field.as_dict()

                # Loop through all patch boundaries
                for boundary_name in patch_boundaries:
                    st.subheader("Patch Boundaries")

                    with st.expander(f"{boundary_name}"):
                        # Get the current boundary condition if it exists
                        if (
                            boundary_name in field_boundary_dict
                            and field_boundary_dict[boundary_name]
                        ):
                            default_Dict = field_boundary_dict[boundary_name]
                        else:
                            default_Dict = {
                                "type": "custom",
                                "value": FIELD_DEFAULT_VALUE[field],
                            }

                        # Select boundary condition type (OUTSIDE the form)
                        current_type = default_Dict.get("type", "custom")
                        selected_bc_type = select_boundary_condition_type(field, boundary_name, current_type)

                        if selected_bc_type != "custom":
                            # Get template for this field and boundary condition type
                            template = get_boundary_condition_template(field, selected_bc_type)

                            # Generate the selected boundary condition with default parameters
                            dict_bc = BoundaryCondition.from_dict(default_Dict)

                            # If the types don't match, use the template but preserve values where possible
                            if dict_bc.type == selected_bc_type:
                                # Create a new boundary condition from template
                                bc = dict_bc
                            else:
                                # Create a new boundary condition from template
                                bc = template

                            # Pre-select Function1 types outside the form
                            bc = preselect_function1_types(field, boundary_name, bc)

                            if bc.type == selected_bc_type:
                                bc.name = f"{boundary_name}_{field}_{bc.type}"


                        # Now create the form for the actual boundary condition values
                        with st.form(f"boundary_conditions_{field}_{boundary_name}"):
                            # Render the appropriate editor based on the selected type
                            if selected_bc_type != "custom":
                                bc = bc.render_ui(field, boundary_name)
                            else:
                                bc = make_custom(field,boundary_name,default_Dict)
                            # Add a submit button for this boundary
                            if st.form_submit_button(f"Save {boundary_name} Boundary Condition"):
                                success, message = save_boundary_condition(field, boundary_name, bc, field_file_path)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)

                # Handle special boundaries automatically
                if empty_boundaries or cyclic_boundaries or symmetry_boundaries:
                    st.subheader("Special Boundaries")

                    # Display non-patch boundaries
                    if empty_boundaries:
                        st.write(f"Empty boundaries: {', '.join(empty_boundaries)}")
                    if cyclic_boundaries:
                        st.write(f"Cyclic boundaries: {', '.join(cyclic_boundaries)}")
                    if symmetry_boundaries:
                        st.write(f"Symmetry boundaries: {', '.join(symmetry_boundaries)}")

                    try:
                        with FoamFieldFile(field_file_path) as field_file:
                            for boundary_name in empty_boundaries:
                                field_file.boundary_field[boundary_name] = {"type": "empty"}
                            for boundary_name in cyclic_boundaries:
                                field_file.boundary_field[boundary_name] = {"type": "cyclic"}
                            for boundary_name in symmetry_boundaries:
                                field_file.boundary_field[boundary_name] = {"type": "symmetryPlane"}
                    except Exception as e:
                        st.error(f"Error updating special boundaries: {str(e)}")
