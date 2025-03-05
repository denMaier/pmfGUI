import streamlit as st
from foamlib import FoamCase
from pathlib import Path
from state import *
from stages.meshAux.helpers import *
from stages.meshAux.make2D import *

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

    if st.button("Generate Geometry"):
        twoDEdgeDictGenerator()
    meshData = get_case_data()["Mesh"]
    if meshData["edgeDict"] is not None:
        meshData["cellSize"] = st.number_input("maxCellSize", value=meshData["cellSize"])
        meshData["nBoundaryLayers"] = st.number_input("nBoundaryLayers", value=meshData["nBoundaryLayers"])
        if st.button("Start Meshing"):
            fmsRibbon = edgesToRibbonFMS(meshData["edgeDict"])
            with open(Path(foamCase)/"system/geometryRibbon.fms", 'w') as f:
                f.write(fmsRibbon)
                print("Wrote the file")
            meshDict["surfaceFile"] = '"system/geometryRibbon.fms"'
            meshDict["maxCellSize"] = meshData["cellSize"]
            meshDict["boundaryLayers"]["nLayers"] = meshData["nBoundaryLayers"]
            try:
                foamCase.run(["cartesian2DMesh"])
                st.success("Mesh created successfully")
            except Exception as e:
                st.error(f"Failed to create mesh: {e}")
