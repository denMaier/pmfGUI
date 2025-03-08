import pyvista as pv
import streamlit as st
from stpyvista import stpyvista
from state import get_case_data
from annotated_text import annotated_text
from pathlib import Path

def init(foam_file: Path) -> None:
    case_data = get_case_data()

    # Create the reader
    case_data["Mesh"]["reader"] = pv.OpenFOAMReader(foam_file)
    ntimes = case_data["Mesh"]["reader"].number_time_points

    # Load the latest time step:
    case_data["Mesh"]["reader"].set_active_time_point(ntimes-1)
    case_data["Mesh"]["reader"].cell_to_point_creation = False

def load_foam_data(foam_file: Path) -> bool:
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

def update_visualization(show_mesh: bool, bg_darkness: float, selected_palette: str) -> None:
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
        palette = get_palette(selected_palette, num_patches)

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
                legend = legend + [tuple([names[i]," ",palette[i]])]

    # Set darker background color
    plotter.background_color = bg_color

    # Final touches
    plotter.set_viewup([0, 1, 0])

    # Send to streamlit
    with st.empty():
        stpyvista(plotter, key="mesh_viz")
    with st.empty():
        annotated_text(legend)

def plot_foam_mesh(foam_file: str, show_mesh: bool, bg_darkness: float, selected_palette: str) -> None:
    """
    Reads a .foam file, extracts the mesh, and plots a 2D view with colorblind-friendly colors.

    Args:
        foam_file: Path to the .foam file.

    Returns:
        None (displays a plot).
    """
    dotFoam = Path(foam_file)

    if get_case_data()["Mesh"]["boundaries"] is None:
        with st.spinner("Loading OpenFOAM data..."):
            # Load the data
            init(dotFoam)
            load_foam_data(dotFoam)
            st.success("Data loaded successfully!")

    # Update visualization (runs every time the app rerenders)
    with st.spinner("Generating visualisation. Please wait..."):
        update_visualization(show_mesh, bg_darkness, selected_palette)

    if st.button("Reload Data"):
        with st.spinner("Reloading OpenFOAM data..."):
            init(dotFoam)
            load_foam_data(dotFoam)
            st.rerun()


def add_visu_sidebar() -> None:
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

def get_palette(selected_palette, n_colors) -> list:
    """
    Returns a color palette as a list of hex codes.

    Args:
        selected_palette (str): The name of the palette ('deep', 'muted', etc.).
        n_colors (int): The number of colors to return.

    Returns:
        list: A list of hex color codes.
    """

    palettes = {
        "deep": ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974", "#64B5CD"],
        "muted": ["#4878CF", "#6ACC65", "#D65F5F", "#956CB4", "#D3C36C", "#8CB4CD"],
        "pastel": ["#A1C9F4", "#B0E57C", "#F28C82", "#D3A4DE", "#FCE29A", "#94D0F5"],
        "bright": ["#0079FA", "#36BC1C", "#EB4034", "#A64DCD", "#FFC71C", "#00C2C7"],
        "dark": ["#001C7F", "#013220", "#8B0909", "#592887", "#A63700", "#3C1098"],
        "colorblind": ["#0072B2", "#009E73", "#D55E00", "#CC79A7", "#F0E442", "#56B4E9"]
    }

    if selected_palette not in palettes:
        raise ValueError(f"Palette '{selected_palette}' not found.")

    palette = palettes[selected_palette]

    # If you need more colors than the base palette provides, you can cycle or interpolate.
    if n_colors > len(palette):
        # Example: Cycle the palette
        repeated_palette = palette * (n_colors // len(palette)) + palette[:(n_colors % len(palette))]
        return repeated_palette
    else:
        return palette[:n_colors]
