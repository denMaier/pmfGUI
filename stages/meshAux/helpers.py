import streamlit as st
import zipfile
import os


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
