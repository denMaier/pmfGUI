import pyvista as pv
import streamlit as st
from stpyvista import stpyvista
import seaborn as sns

@st.fragment
def plot_foam_mesh(foam_file):
    """
    Reads a .foam file, extracts the mesh, and plots a 2D view with colorblind-friendly colors.
    
    Args:
        foam_file: Path to the .foam file.
    
    Returns:
        None (displays a plot).
    """
    # Create the reader
    reader = pv.OpenFOAMReader(foam_file)
    
    # Disable the internal mesh - this is the key step
    reader.disable_patch_array("internalMesh")
    
    # Make sure all boundary patches are enabled
    patch_names = [name for name in reader.patch_array_names if name != "internalMesh"]
    for patch in patch_names:
        reader.enable_patch_array(patch)
    
    # Read the data
    data = reader.read()
    boundaries = data["boundary"]
    
    # UI Controls
    st.sidebar.header("Visualization Options")
    show_mesh = st.sidebar.checkbox("Show Mesh Lines", value=True)
    bg_darkness = st.sidebar.slider("Background Darkness", min_value=0.1, max_value=0.4, value=0.25, step=0.05)
    
    # Seaborn palette selection
    palette_options = ["muted", "deep", "colorblind", "pastel", "dark", "bright"]
    selected_palette = st.sidebar.selectbox("Color Palette", palette_options, index=0)
    
    # Calculate background color based on slider (darker gray)
    bg_value = 1.0 - bg_darkness
    bg_color = (bg_value, bg_value, bg_value)
    
    # Create a plotter
    plotter = pv.Plotter()
    
    # If the data is a MultiBlock, extract each patch and add with different colors
    if isinstance(boundaries, pv.MultiBlock):
        names = list(boundaries.keys())
        num_patches = len(names)
        
        # Get colors from seaborn palette
        # Note: seaborn returns RGB values in 0-1 range, perfect for PyVista
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
        
        # Add a legend with slightly darker background
        plotter.add_legend(bcolor=(0.8, 0.8, 0.8, 0.5))
    
        # Set darker background color
        plotter.background_color = bg_color
        
        # Final touches
        plotter.view_isometric()
        
        ## Send to streamlit
        #stpyvista(plotter, key="basic_mesh")