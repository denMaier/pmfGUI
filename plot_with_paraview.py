import pyvista as pv
import streamlit as st
from stpyvista import stpyvista
import seaborn as sns
from state import get_case_data
from annotated_text import annotated_text

def init(foam_file):
    case_data = get_case_data()

    # Create the reader
    case_data["Mesh"]["reader"] = pv.OpenFOAMReader(foam_file)
    ntimes = case_data["Mesh"]["reader"].number_time_points

    # Load the latest time step:
    case_data["Mesh"]["reader"].set_active_time_point(ntimes-1)
    case_data["Mesh"]["reader"].cell_to_point_creation = False

def load_foam_data(foam_file):
    """
    Reads a .foam file and extracts the mesh data.
    This function only needs to run once per file.

    Args:
        foam_file: Path to the .foam file.
    """
    case_data = get_case_data()

    # Read the data
    data = case_data["Mesh"]["reader"].read()
    case_data["Mesh"]["internal"] = data["internalMesh"]
    case_data["Mesh"]["boundaries"] = data["boundary"]

    return True

def update_visualization(show_mesh: bool, bg_darkness: float, selected_palette: str):
    """
    Updates the visualization based on the current parameters.
    This function runs whenever a parameter changes.
    """
    case_data = get_case_data()
    if case_data["Mesh"]["boundaries"] is None:
        return

    # Calculate background color
    bg_value = 1.0 - bg_darkness
    bg_color = (bg_value, bg_value, bg_value)

    # Get the plotter
    plotter = pv.Plotter(lighting='none')

    # --- Clear Existing Actors ---
    #plotter.clear()

    boundaries = case_data["Mesh"]["boundaries"]

    # If the data is a MultiBlock, extract each patch and add with different colors
    legend = []
    if isinstance(boundaries, pv.MultiBlock):
        names = list(boundaries.keys())
        num_patches = len(names)

        # Get colors from seaborn palette
        palette = sns.color_palette(selected_palette, n_colors=num_patches)

        # Add each patch to the plotter with a different color
        for i, block in enumerate(boundaries):
            if block.n_points > 0:  # Skip empty blocks
                plotter.add_mesh(
                    block,
                    color=palette[i],
                    label=names[i],
                    show_edges=show_mesh,
                    line_width=1.0
                )
                legend = legend + [tuple([names[i]," ",palette.as_hex()[i]])]

    # Set darker background color
    plotter.background_color = bg_color

    # Final touches
    plotter.set_viewup([0, 1, 0])

    # Send to streamlit
    with st.empty():
        stpyvista(plotter, key="mesh_viz")
    with st.empty():
        annotated_text(legend)

def plot_foam_mesh(foam_file: str, show_mesh: bool, bg_darkness: float, selected_palette: str):
    """
    Reads a .foam file, extracts the mesh, and plots a 2D view with colorblind-friendly colors.

    Args:
        foam_file: Path to the .foam file.

    Returns:
        None (displays a plot).
    """

    if get_case_data()["Mesh"]["boundaries"] is None:
        with st.spinner("Loading OpenFOAM data..."):
            # Load the data
            init(foam_file)
            load_foam_data(foam_file)
            st.success("Data loaded successfully!")

    # Update visualization (runs every time the app rerenders)
    with st.spinner("Generating visualisation. Please wait..."):
        update_visualization(show_mesh, bg_darkness, selected_palette)

    if st.button("Reload Data"):
        with st.spinner("Reloading OpenFOAM data..."):
            load_foam_data(foam_file)

def add_visu_sidebar():
    with st.sidebar:

            # Sidebar controls
            st.header("Visualization Options")

            vis = st.session_state.vis

            # Update session state based on sidebar inputs and trigger callback
            vis["show_mesh"] = st.toggle(
                "Show Mesh Lines",
                value=vis["show_mesh"]
            )

            # Seaborn palette selection
            palette_options = ["muted", "deep", "colorblind", "pastel", "dark", "bright"]
            vis["selected_palette"] = st.selectbox(
                "Color Palette",
                palette_options,
                index=palette_options.index(vis["selected_palette"])
            )

            vis["bg_darkness"] = st.slider(
                "Background Darkness",
                min_value=0.1,
                max_value=0.4,
                value=vis["bg_darkness"],
                step=0.05
            )
