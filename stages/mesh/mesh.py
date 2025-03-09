import streamlit as st
from foamlib import FoamCase
from pathlib import Path
from state import *get_case,
from stages.mesh.helpers import *
from stages.mesh.make2D import *
import pyvista as pv
from plotting_helpers import get_openfoam_visualizer

@st.fragment
def main3D():
    foamCase = get_case()

    select_method(
        foamCase,
        ["OpenFoam", "BlockMesh", "Gmsh", "Geometry"],
        [
            "'.zip' file with contents of 'polyMesh' on top level",
            "a 'blockMeshDict' file",
            "Gmsh's '.geo' file",
            "'.stl' files from a CAD program",
        ],
        3
    )
    #set_boundary_types()

@st.fragment
def main2D():
    foamCase = get_case()

    select_method(
        foamCase,
        ["OpenFoam", "Gmsh", "Generate Now"],
        [
            "'.zip' file with contents of 'polyMesh' on top level",
            "Gmsh's '.geo' file",
            "Start a mesh generation workflow"
        ],
        2
    )

def select_method(foamCase: FoamCase, input_types, captions, dimensions):
    polyMeshPath = Path(foamCase)/"constant/polyMesh"

    input_type = st.radio(
        "Select how you want to supply the mesh data",
        input_types,
        captions=captions,
        key=f"mesh_input_type_{dimensions}D"  # Add a key to the radio button
    )

    if input_type == "OpenFoam":
        meshFile = st.file_uploader("polyMesh.zip",type=['zip'], key=f"ofmesh_uploader_type_{dimensions}D")
        if  meshFile is not None:
            extract_zip(meshFile,polyMeshPath)
            get_case_data()["Mesh"]["available"] = True
    elif input_type == "BlockMesh":
        meshFile = st.file_uploader("blockMeshDict", key=f"blockmesh_uploader_{dimensions}D")
        if meshFile is not None:
            if meshFile.name != "blockMeshDict":
                st.warning("Name of file is not 'blockMeshDict', will try with renamed file")
            # Corrected save path:
            save_path = Path(foamCase) / "system"
            success, saved_path = save_uploaded_file(meshFile, save_path,"blockMeshDict")
            if success:
                st.success(f"Saved the mesh into {saved_path}")
                foamCase.block_mesh()
                get_case_data()["Mesh"]["available"] = True
            else:
                st.error("Failed to save blockMeshDict")
    elif input_type == "Gmsh":
        meshFile = st.file_uploader("Gmsh .geo file", type=['geo'], key=f"gmsh_uploader_{dimensions}D")
        if meshFile is not None:
            save_path = Path(foamCase)
            success, saved_path = save_uploaded_file(meshFile,Path(foamCase),"mesh.geo")
            if success:
                st.success(f"Saved the mesh into {saved_path}")

                with st.status("Generating mesh...", expanded=True) as status:
                    st.write("Meshing...")
                    foamCase.run("gmsh -3 mesh.geo") # You need to implement this

                    # Check if mesh.msh was created
                    msh_file = Path(foamCase) / "mesh.msh"
                    if not msh_file.exists():
                        st.error("Gmsh failed to generate mesh.msh")

                    st.write("Converting to OpenFoam mesh...")
                    foamCase.run("gmshToFoam mesh.msh") # You need to implement this

                    if polyMeshPath.exists():
                        status.update(
                            label="Mesh generation complete!", state="complete", expanded=False
                        )
                    else:
                        status.error("An Error occured!")
            else:
                st.error("Failed to save .geo file")


    elif input_type == "Geometry":
        st.warning("Not yet implemented, sorry..")

    elif input_type == "Generate Now":
        make2DMesh(foamCase)

def set_boundary_types():
    boundaryDict = get_file("boundary")
    for key, value in boundaryDict.as_dict().items():
        with st.expander(f"{key} \t type"):
            st.write("Comming soon")

def make2DMesh(foamCase: FoamCase):
    """
    Extracts mesh data from an OpenFOAM edgeDict,
    handling variations in whitespace, line breaks, and the FoamFile header.
    """
    meshDict = foamCase.file("system/meshDict")

    if not Path(meshDict).exists():
        st.error("There is no meshDict file")
        return

    meshData = get_case_data()["Mesh"]
    edgeDict = meshData["edgeDict"]
    if Path(get_case().file("system/edgeDict")).exists():
        meshData["edgeDict"] = get_case().file("system/edgeDict").as_dict()

    if st.button("Generate Geometry"):
        twoDEdgeDictGenerator()
    if edgeDict:
        with st.form("Meshing2D"):
            meshData["cellSize"] = st.number_input("maxCellSize", value=meshData["cellSize"])
            meshData["nBoundaryLayers"] = st.number_input("nBoundaryLayers", value=meshData["nBoundaryLayers"])
            if st.form_submit_button("Start Meshing"):
                fmsRibbon = edgesToRibbonFMS(get_case().file("system/edgeDict").as_dict())
                with open(Path(foamCase)/"system/geometryRibbon.fms", 'w') as f:
                    f.write(fmsRibbon)
                meshDict["surfaceFile"] = '"system/geometryRibbon.fms"'
                meshDict["maxCellSize"] = meshData["cellSize"]
                meshDict["boundaryLayers"]["nLayers"] = meshData["nBoundaryLayers"]
                try:
                    foamCase.run(["cartesian2DMesh"])
                    st.success("Mesh created successfully")
                except Exception as e:
                    st.error(f"Failed to create mesh: {e}")

def plot_foam_mesh(case_path, show_mesh=True, bg_darkness=0.35,
                  selected_palette="deep", style="surface",
                  color_patches=False, show_boundaries=True,
                  only_boundaries=False, opacity=1.0):
    """
    Plot the OpenFOAM mesh with the selected visualization options.

    Parameters:
        case_path: Path to the OpenFOAM case
        show_mesh: Whether to show mesh edges
        bg_darkness: Background darkness (0.1-0.4)
        selected_palette: Color palette to use
        style: Mesh style (surface, wireframe, points)
        color_patches: Whether to color patches differently
        show_boundaries: Whether to show boundary patches
        only_boundaries: Whether to show only boundary patches
        opacity: Opacity of the mesh (0.1-1.0)
    """
    # Get the background color based on darkness
    bg_value = 1.0 - bg_darkness
    bg_color = (bg_value, bg_value, bg_value)

    # Get the visualizer instance (cached)
    visualizer = get_openfoam_visualizer(case_path)

    # Force refresh if the case has changed
    if visualizer.has_case_changed():
        with st.spinner("Case has changed - refreshing data..."):
            visualizer.refresh()

    # Create a PyVista plotter for Streamlit
    plotter = pv.Plotter()
    plotter.background_color = bg_color

    # Get the custom colormap for this plot
    cmap = visualizer.COLOR_PALETTES.get(selected_palette, visualizer.COLOR_PALETTES["deep"])

    # Edge color based on background
    edge_color = 'black' if bg_darkness < 0.25 else 'white'

    # Actually visualize the mesh
    visualizer.visualize_mesh(
        plotter=plotter,
        show_edges=show_mesh,
        style=style,
        color_patches=color_patches,
        show_boundaries=show_boundaries,
        only_boundaries=only_boundaries,
        opacity=opacity,
        edge_color=edge_color,
        boundary_palette=selected_palette
    )

    # Set a nice camera position
    plotter.view_isometric()

    # Render in Streamlit using stpyvista
    stpyvista(plotter, key="mesh_viz")
