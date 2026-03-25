from pathlib import Path

from foamlib import FoamCase
import pyvista as pv
import streamlit as st
import streamlit.components.v1 as components

from alpha_runtime import get_mesh_workflow_report
from plotting_helpers import get_openfoam_visualizer
from stages.mesh.helpers import extract_zip, save_uploaded_file
from stages.mesh.make2D import edgesToRibbonFMS, twoDEdgeDictGenerator
from state import get_case, get_case_data


@st.fragment
def main3D():
    foamCase = get_case()

    select_method(
        foamCase,
        ["OpenFoam", "BlockMesh", "Gmsh", "Geometry"],
        [
            "Import an existing polyMesh.zip",
            "Upload system/blockMeshDict and run blockMesh",
            "Experimental mesh generation from .geo",
            "Experimental geometry-driven meshing",
        ],
        3,
    )


@st.fragment
def main2D():
    foamCase = get_case()

    select_method(
        foamCase,
        ["OpenFoam", "Gmsh", "Generate Now"],
        [
            "Import an existing polyMesh.zip",
            "Experimental mesh generation from .geo",
            "Use the current cartesian2DMesh workflow",
        ],
        2,
    )


def select_method(foamCase: FoamCase, input_types, captions, dimensions):
    poly_mesh_path = Path(foamCase) / "constant/polyMesh"

    input_type = st.radio(
        "Select how you want to supply the mesh data",
        input_types,
        captions=captions,
        key=f"mesh_input_type_{dimensions}D",
    )

    if input_type == "OpenFoam":
        st.caption(f"Import target: {poly_mesh_path}")
        mesh_file = st.file_uploader("polyMesh.zip", type=["zip"], key=f"ofmesh_uploader_type_{dimensions}D")
        if mesh_file is not None:
            extract_zip(mesh_file, poly_mesh_path)
    elif input_type == "BlockMesh":
        render_block_mesh(foamCase, dimensions)
    elif input_type == "Gmsh":
        render_experimental_mesh_workflow(
            "Gmsh mesh generation is experimental and disabled in alpha.",
            "Use OpenFOAM mesh import, blockMesh, or the supported 2D workflow instead.",
            key_suffix=f"gmsh_{dimensions}D",
        )
    elif input_type == "Geometry":
        render_experimental_mesh_workflow(
            "Geometry-based mesh generation is experimental and disabled in alpha.",
            "This roadmap item stays visible, but it cannot be executed in the alpha build.",
            key_suffix=f"geometry_{dimensions}D",
        )
    elif input_type == "Generate Now":
        make2DMesh(foamCase)


def render_block_mesh(foamCase: FoamCase, dimensions: int) -> None:
    report = get_mesh_workflow_report(Path(foamCase), "blockMesh")
    block_mesh_dict_path = Path(foamCase) / "system" / "blockMeshDict"

    st.caption(f"Save path: {block_mesh_dict_path}")
    if report.details.get("resolved_executable"):
        st.caption(f"Executable: {report.details['resolved_executable']}")
    else:
        st.caption("Executable: blockMesh (not currently available on PATH)")

    mesh_file = st.file_uploader("blockMeshDict", key=f"blockmesh_uploader_{dimensions}D")
    if mesh_file is not None:
        if mesh_file.name != "blockMeshDict":
            st.warning("The uploaded file will be saved as blockMeshDict.")

        save_path = Path(foamCase) / "system"
        success, saved_path = save_uploaded_file(mesh_file, save_path, "blockMeshDict", overwrite=True)
        if success:
            st.success(f"Saved blockMeshDict to {saved_path}")
        else:
            st.error("Failed to save blockMeshDict")

    if not report.ready:
        for issue in report.blocking_issues:
            st.error(issue.message)

    if not block_mesh_dict_path.exists():
        st.info("Upload a blockMeshDict or provide one in system/blockMeshDict to enable blockMesh.")

    if st.button(
        "Run blockMesh",
        key=f"run_blockmesh_{dimensions}D",
        disabled=(not report.ready or not block_mesh_dict_path.exists()),
        type="primary",
    ):
        try:
            foamCase.block_mesh()
            st.success("blockMesh completed successfully.")
        except Exception as exc:
            st.error(f"blockMesh failed: {exc}")


def render_experimental_mesh_workflow(message: str, detail: str, key_suffix: str) -> None:
    st.warning(message)
    st.caption(detail)
    st.file_uploader("Experimental input", disabled=True, key=f"disabled_upload_{key_suffix}")
    st.button("Execute Experimental Workflow", disabled=True, key=f"disabled_button_{key_suffix}")


def make2DMesh(foamCase: FoamCase):
    """
    Extracts mesh data from an OpenFOAM edgeDict,
    handling variations in whitespace, line breaks, and the FoamFile header.
    """
    mesh_dict = foamCase.file("system/meshDict")

    if not Path(mesh_dict).exists():
        st.error("There is no meshDict file")
        return

    mesh_data = get_case_data()["Mesh"]
    edgeDict = mesh_data["edgeDict"]
    edge_dict_path = Path(get_case().file("system/edgeDict"))
    if edge_dict_path.exists():
        mesh_data["edgeDict"] = get_case().file("system/edgeDict").as_dict()
        edgeDict = mesh_data["edgeDict"]

    report = get_mesh_workflow_report(Path(foamCase), "cartesian2DMesh")
    if report.details.get("resolved_executable"):
        st.caption(f"Executable: {report.details['resolved_executable']}")
    else:
        st.caption("Executable: cartesian2DMesh (not currently available on PATH)")

    if not report.ready:
        for issue in report.blocking_issues:
            st.error(issue.message)

    if st.button("Generate Geometry"):
        twoDEdgeDictGenerator()

    if edgeDict:
        with st.form("Meshing2D"):
            mesh_data["cellSize"] = st.number_input("maxCellSize", value=mesh_data["cellSize"])
            mesh_data["nBoundaryLayers"] = st.number_input("nBoundaryLayers", value=mesh_data["nBoundaryLayers"])
            should_start = st.form_submit_button("Start Meshing", type="primary", disabled=not report.ready)
            if should_start:
                fmsRibbon = edgesToRibbonFMS(get_case().file("system/edgeDict").as_dict())
                with open(Path(foamCase) / "system/geometryRibbon.fms", "w") as handle:
                    handle.write(fmsRibbon)
                with mesh_dict:
                    mesh_dict["surfaceFile"] = '"system/geometryRibbon.fms"'
                    mesh_dict["maxCellSize"] = mesh_data["cellSize"]
                    mesh_dict["boundaryLayers"]["nLayers"] = mesh_data["nBoundaryLayers"]
                try:
                    foamCase.run(["cartesian2DMesh"])
                    st.success("Mesh created successfully")
                except Exception as exc:
                    st.error(f"Failed to create mesh: {exc}")
    else:
        st.info("Generate or load an edgeDict to enable the supported 2D meshing workflow.")


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
    bg_value = 1.0 - bg_darkness
    bg_color = (bg_value, bg_value, bg_value)

    visualizer = get_openfoam_visualizer(case_path)

    if visualizer.has_case_changed():
        with st.spinner("Case has changed - refreshing data..."):
            visualizer.refresh()

    plotter = pv.Plotter(off_screen=True)
    plotter.background_color = bg_color

    cmap = visualizer.COLOR_PALETTES.get(selected_palette, visualizer.COLOR_PALETTES["deep"])

    edge_color = "black" if bg_darkness < 0.25 else "white"

    visualizer.visualize_mesh(
        plotter=plotter,
        show_edges=show_mesh,
        style=style,
        color_patches=color_patches,
        show_boundaries=show_boundaries,
        only_boundaries=only_boundaries,
        opacity=opacity,
        edge_color=edge_color,
        boundary_palette=selected_palette,
    )

    plotter.view_isometric()

    try:
        html_buffer = plotter.export_html(None)
    except ImportError as exc:
        st.error("PyVista HTML export is unavailable. Please install the Trame dependencies.")
        st.caption(str(exc))
        plotter.close()
        return

    components.html(html_buffer.getvalue(), height=700, scrolling=False)
    plotter.close()
