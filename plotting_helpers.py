import streamlit as st
from OpenFOAMVisualizer import OpenFOAMVisualizer

# Create a singleton visualizer to ensure we only create one instance
# This helps with caching and performance
@st.cache_resource
def get_openfoam_visualizer(case_path):
    """Get a cached OpenFOAM visualizer for the case."""
    return OpenFOAMVisualizer(case_path)

# Define custom color palettes
COLOR_PALETTES = [
    "deep",
    "muted",
    "pastel",
    "bright",
    "dark",
    "colorblind"
]

def add_visu_sidebar():
    """Add visualization controls to the sidebar."""
    with st.sidebar:
        st.header("Visualization Options")

        vis = st.session_state.vis

        # Update session state based on sidebar inputs
        vis["show_mesh"] = st.toggle(
            "Show Mesh Lines",
            value=vis["show_mesh"]
        )

        # Palette selection
        palette_options = list(COLOR_PALETTES)
        vis["selected_palette"] = st.selectbox(
            "Color Palette",
            palette_options,
            index=palette_options.index(vis["selected_palette"]) if vis["selected_palette"] in palette_options else 0
        )

        vis["bg_darkness"] = st.slider(
            "Background Darkness",
            min_value=0.1,
            max_value=0.4,
            value=vis["bg_darkness"],
            step=0.05
        )

        vis["style"] = st.radio(
            "Mesh Style",
            ["surface", "wireframe", "points"],
            index=0
        )

        vis["color_patches"] = st.toggle(
            "Color Patches",
            value=vis["color_patches"]
        )

        vis["show_boundaries"] = st.toggle(
            "Show Boundaries",
            value=vis["show_boundaries"]
        )

        vis["only_boundaries"] = st.toggle(
            "Only Boundaries",
            value=vis["only_boundaries"]
        )

        vis["opacity"] = st.slider(
            "Opacity",
            min_value=0.1,
            max_value=1.0,
            value=vis["opacity"],
            step=0.1
        )
