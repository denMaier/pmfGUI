import streamlit as st
from foamlib import FoamCase
from pathlib import Path
from state import get_case, get_case_data, get_path, has_mesh
import os
import re
import zipfile
#import fluidfoam 
#from matplotlib import pyplot as plt
#from matplotlib.collections import LineCollection

def load_case_cell_zones(foamCase: FoamCase):
    """
    Extracts cellZone names from an OpenFOAM cellZones file,
    handling variations in whitespace, line breaks, and the FoamFile header.

    Args:

    Returns:
        list: A list of cellZone names (strings). Returns an empty list if no
              cellZones are found or if an error occurs.
    """
    filePath = Path(foamCase) / get_path("Mesh","cellZones")
    
    if not filePath.exists():
        st.warning("No CellZones exist! Please create at least one cellZone!")
        return 
    
    try:
        with filePath.open() as f:
            content = f.read()

        # Regex to find cellZone names, robust to whitespace and header.
        # We now skip the FoamFile header section.
        match = re.search(r"FoamFile\s*\{.*?\}\s*(.*)", content, re.DOTALL)
        if match:
            content_after_header = match.group(1)
            matches = re.findall(r'(\w+)\s*\{', content_after_header)
            for zonematch in matches:
                get_case_data()["Mesh"]["cellZones"][zonematch] = {
                    "type": None,
                    "parameters": {}
                }
        else:
            st.error("No cellZones in cellZone file found!!")
        
    except FileNotFoundError:
        print(f"Error: File not found at {filePath}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def load_boundary(foamCase: FoamCase):
    """
    Args:

    Returns:

    """
    filePath = Path(foamCase) / get_path("Mesh","boundary")
    
    if not filePath.exists():
        st.warning("No mesh exists!")
        return 

    boundaryFile = foamCase.file(filePath)
    get_case_data()["Mesh"]["boundary"] = dict(boundaryFile.as_dict()[None])
    
def entry():
    foamCase = get_case()
    
    col1, col2 = st.columns(2)
    
    with col1:
        upload_mesh(foamCase)
        
        load_boundary(foamCase)
        load_case_cell_zones(foamCase)

        set_boundary_types()
    
        

def upload_mesh(foamCase: FoamCase):
    
    input_type = st.radio(
        "Select how you want to supply the mesh data",
        ["OpenFoam", "BlockMesh", "Gmsh", "Geometry"],
        captions=[
            "'.zip' file with contents of 'polyMesh' on top level",
            "a 'blockMeshDict' file",
            "Gmsh's '.geo' file",
            "'.stl' file from a CAD program",
        ],
        key="mesh_input_type"  # Add a key to the radio button
    )
            
    polyMeshPath = Path(foamCase)/get_path("Mesh","polyMesh")
    
    if input_type == "OpenFoam":
        meshFile = st.file_uploader("polyMesh.zip",type=['zip'], key="polymesh_uploader")
        if  meshFile is not None:
            extract_zip(meshFile,polyMeshPath)
            get_case_data()["Mesh"]["available"] = True
    elif input_type == "BlockMesh":
        meshFile = st.file_uploader("blockMeshDict", key="blockmesh_uploader")
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
        meshFile = st.file_uploader("Gmsh .geo file", type=['geo'], key="gmsh_uploader")
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
                        get_case_data()["Mesh"]["available"] = True
                        status.update(
                            label="Mesh generation complete!", state="complete", expanded=False
                        )
                    else:
                        status.update(
                            label="An Error occured!", state="Error", expanded=False
                        )
                    
            else:
                st.error("Failed to save .geo file")
                

    elif input_type == "Geometry":
        st.warning("Not yet implemented, sorry..")
    
    

def extract_zip(meshFile, polyMeshLoc):
  """
  Extracts a .zip file to a specified location.

  Args:
    meshFile:  The path to the .zip file (string), or a file-like object.
    polyMeshLoc: The directory where the contents of the .zip file should be extracted.
                   This directory will be created if it doesn't exist.
  """
  try:
    # Create the target directory if it doesn't exist
    os.makedirs(polyMeshLoc, exist_ok=True)

    # Open the zip file.  Handles both path strings and file-like objects.
    with zipfile.ZipFile(meshFile, 'r') as zip_ref:
      # Extract all files to the specified directory
      zip_ref.extractall(polyMeshLoc)

    print(f"Successfully extracted contents of {meshFile} to {polyMeshLoc}")

  except FileNotFoundError:
    print(f"Error: Zip file not found: {meshFile}")
  except zipfile.BadZipFile:
    print(f"Error: Invalid zip file: {meshFile}")
  except Exception as e:
    print(f"An unexpected error occurred: {e}")

  st.success(f'Saved the mesh into {polyMeshLoc}')
  
def save_uploaded_file(uploadedfile, destination_folder, new_file_name):
    """
    Combines saving an uploaded file and renaming it.  This handles the
    in-memory nature of the UploadedFile object correctly.

    Args:
        uploadedfile: The UploadedFile object from st.file_uploader.
        destination_folder: The path to save the file in.
        new_file_name:  The new name for the file (including extension).

    Returns:
        bool:  True on success, False on failure.
        str or None: The full path to the renamed file, or None if failed.
    """
    if uploadedfile is None:
        return False, None

    if not os.path.exists(destination_folder):
        try:
            os.makedirs(destination_folder)
        except OSError as e:
            st.error(f"Error creating directory: {e}")
            return False, None

    # Construct the full *new* file path
    new_file_path = os.path.join(destination_folder, new_file_name)
    
    # Check if a file with the *new* name already exists
    if os.path.exists(new_file_path):
        st.error(f"Error: A file with the name '{new_file_name}' already exists in '{destination_folder}'.")
        return False, None

    try:
        # Write the uploaded file content to the *new* file path.
        # This combines saving and renaming.
        with open(new_file_path, "wb") as f:
            f.write(uploadedfile.getbuffer())

        st.success(f"File uploaded and renamed to: {new_file_path}")
        return True, new_file_path

    except Exception as e:
        st.error(f"Error saving/renaming file: {e}")
        return False, None
    
def set_boundary_types():
    boundaryDict = get_case_data()["Mesh"]["boundary"]
    for key, value in boundaryDict.items():
        st.expander(key+"\t"+"type")

'''       
@st.fragment    
def plot_mesh():
    foamcase = get_case()
    if st.button("Plot mesh"):
        if has_mesh():
            planes = ["xy","xz","yz"]
            fig, ax = plt.subplots()
            MyMesh = fluidfoam.MeshVisu(path = Path(foamcase),plane="xy")
            ln_coll = LineCollection(MyMesh.get_all_edgesInBox())
            ax.add_collection(ln_coll, autolim=True)
            st.pyplot(fig)
    
            fig, ax = plt.subplots(nrows=3,ncols=1)
            for i, orientation in enumerate(planes):
                MyMesh = fluidfoam.MeshVisu(path = Path(foamcase),plane=orientation)
                #MyMesh.set_box_to_mesh_size()
                ln_coll = LineCollection(MyMesh.get_all_edgesInBox(),axes=ax[i])
                #ax[i].add_collection(ln_coll, autolim=True)
                st.pyplot(fig)
 
        else:
            st.error("No mesh loaded yet!")
'''