import streamlit as st
import pandas as pd
import altair as alt
import json

from vtkmodules.vtkCommonDataModel import vtkVertex
from state import *

@st.dialog("2D Mesh Generator", width="large")
def twoDEdgeDictGenerator():
    mesh_data = get_case_data()["Mesh"]
    case = get_case()
    edgeDict = mesh_data["edgeDict"]

    # --- Vertex Input ---
    with st.form("vertices_form"):
        st.header("1. Define Vertices")
        st.write("Enter the x and y coordinates for each vertex.")

        if 'vertices' in edgeDict and mesh_data['df_vertices'] is None:
            data =  edgeDict["vertices"]
            mesh_data['df_vertices'] = pd.DataFrame(data, columns=['x', 'y'])
        elif mesh_data['df_vertices'] is None:
            data = {'x': [0.0], 'y': [0.0]}
            mesh_data['df_vertices'] = pd.DataFrame(data)

        col1, col2 = st.columns([1, 3])

        column_config = {
            "x": st.column_config.NumberColumn("x", format="%.2f", required=True),
            "y": st.column_config.NumberColumn("y", format="%.2f", required=True)
        }

        with col1:
            edited_df_vertices = st.data_editor(
                mesh_data['df_vertices'], num_rows="dynamic", key="data_editor_vertices",
                hide_index = False,
                column_config = column_config
            )
            mesh_data['df_vertices'] = edited_df_vertices

        with col2:
            if st.form_submit_button("Submit Vertices"):
                edgeDict['vertices'] = edited_df_vertices[['x', 'y']].values.tolist()
                st.success("Vertices submitted!")

            if not mesh_data['df_vertices'].empty:
                plot_df = mesh_data['df_vertices'].copy()
                plot_df['index'] = plot_df.index
                c = alt.Chart(plot_df).mark_circle(size=100).encode(x="x", y="y")
                text = alt.Chart(plot_df).mark_text(align="left", baseline="middle", dx=7, color='white').encode(x="x", y="y", text="index")
                st.altair_chart(c + text, use_container_width=True)
            else:
                st.write("Enter vertex data to see the plot.")

    # --- Edge Input ---
    if 'vertices' in edgeDict:
        with st.form("edges_form"):
            st.header("2. Define Edges")
            st.write("Enter the vertex indices that define each edge.")

            if 'edges' in edgeDict and mesh_data['df_edges'] is None:
                edges_data = edgeDict["edges"]
                mesh_data['df_edges'] = pd.DataFrame(edges_data, columns=['P1', 'P2'])
            elif mesh_data['df_edges'] is None:
                edges_data = {'P1': [0], 'P2': [1]}
                mesh_data['df_edges'] = pd.DataFrame(edges_data)

            col1, col2 = st.columns([1, 3])


            vertices_indexes = mesh_data['df_vertices'].index.tolist()

            column_config= {
                "P1": st.column_config.SelectboxColumn("P1", options=vertices_indexes, required=True),
                "P2": st.column_config.SelectboxColumn("P2", options=vertices_indexes, required=True)
            }

            with col1:
                edited_df_edges = st.data_editor(
                    mesh_data['df_edges'], num_rows="dynamic", key="data_editor_edges",
                    column_config= column_config,
                    hide_index = True
                )
                mesh_data['df_edges'] = edited_df_edges

            with col2:
                if st.form_submit_button("Submit Edges"):
                    edgeDict['edges'] = edited_df_edges[['P1', 'P2']].to_numpy(dtype=int).tolist()
                    st.success("Edges submitted!")

                if not mesh_data['df_vertices'].empty and edgeDict['edges']:  # Check for existence AND non-empty
                    # --- Altair Plotting (Vertices and Edges) ---
                    plot_df = mesh_data['df_vertices'].copy()
                    plot_df['index'] = plot_df.index

                    # 1. Vertex Circles
                    points = alt.Chart(plot_df).mark_circle(size=100).encode(x="x", y="y")

                    # 2. Vertex Labels
                    text = alt.Chart(plot_df).mark_text(align="left", baseline="middle", dx=7, color='white').encode(x="x", y="y", text="index")

                    # 3. Edge Lines (using a separate DataFrame)
                    edges_list = []
                    for edge in edgeDict['edges']:
                        try:
                            x1, y1 = tuple(edgeDict['vertices'][edge[0]])
                            x2, y2 = tuple(edgeDict['vertices'][edge[1]])
                            edges_list.append({'x': x1, 'y': y1, 'x2': x2, 'y2': y2, 'edge_id': f"{edge}"}) #create a unique id
                        except IndexError:
                            st.warning("Invalid edge index. Please check your edge definitions.")
                            #Crucially, don't break here.  Continue processing other edges.
                            continue # Go to the next iteration of the loop.

                    if edges_list:  # Check if edges_list is not empty
                        edges_df = pd.DataFrame(edges_list)

                        lines = alt.Chart(edges_df).mark_line(color='red').encode(
                            x='x',
                            y='y',
                            x2='x2',
                            y2='y2',
                            detail='edge_id' # Important:  This tells Altair that each edge is a separate line.
                        )
                        st.altair_chart(points + text + lines, use_container_width=True)
                    else:
                        st.altair_chart(points+text, use_container_width=True) #show the vertices in case no edges can be drawn

                elif 'edges' in edgeDict and not edgeDict['edges']:
                    st.write("No edges defined.") #Specific message if no edges were entered
                else:
                     st.write("Submit Edges to display the plot.")

    # 3. Input: Boundary Patches
    if 'vertices' in edgeDict and 'edges' in edgeDict:
        with st.container(border=True):
            st.header("3. Define Boundary Patches")
            st.write("Define the boundary patches, their types, and the edges associated with them.")

            if 'boundary' in edgeDict and edgeDict['boundary']:
                defaultNames = list(edgeDict['boundary'].keys())
                default_num = len(defaultNames)
            else:
                default_num = 1
                defaultNames = []

            num_patches = st.number_input("Number of Boundary Patches", min_value=0, max_value=10, value=default_num, step=1)

            with st.form("boundary_form", border=False):
                patches = {}
                for i in range(num_patches):
                    st.subheader(f"Patch {i+1}")
                    if i < len(defaultNames):
                        defaultName = defaultNames[i]
                        defaultEdges = []
                        for edgeindex in edgeDict['boundary'][defaultName]['edges']:
                            defaultEdges.append(edgeDict['edges'][edgeindex])
                        defaultPatchType =  edgeDict['boundary'][defaultName]['type']
                    else:
                        defaultName = f"Patch{i+1}"
                        defaultEdges = []
                        defaultPatchType = []

                    patch_name = st.text_input(f"Patch Name:", value=defaultName, key=f"name_{i}")
                    patch_type = st.segmented_control(f"Patch Type:", options=['patch', 'symmetryPlane', 'empty', 'cyclic'], default=defaultPatchType, key=f"type_{i}")

                    edge_names = st.pills(f"Edge Indices for Patch {i+1}", edgeDict['edges'], selection_mode="multi", default=defaultEdges, key=f"edge_{i}")

                    edge_indices = []
                    for edge_name in edge_names:
                        edge_indices.append(edgeDict['edges'].index(edge_name))

                    patches[patch_name] = {
                        'type': patch_type,
                        'edges': edge_indices
                    }

                if st.form_submit_button("Submit Boundary Patches"):
                    edgeDict['boundary'] = {}
                    edgeDict['boundary'] = patches


    # 4. Generate the Dictionary
    if 'vertices' in edgeDict and 'edges' in edgeDict and 'boundary' in edgeDict:
        st.header("4. Generated Dictionary")
        if st.button("Write Dict"):
            edgeDictFile = case.file("system/edgeDict")
            if not Path(edgeDictFile).exists():
                Path(edgeDictFile).touch()
            with edgeDictFile:
                for key, value in edgeDict.items():
                    if isinstance(value, dict):
                        edgeDictFile[key] = {}
                edgeDictFile.update(edgeDict)
            st.rerun()

        with st.expander("Here is the generated dictionary:"):
            st.json(edgeDict)




@st.cache_data
def edgesToRibbonFMS(input_dict):
    """
    Converts a dictionary of vertices, edges, and boundary into an FMS format string.

    Args:
        input_dict: A dictionary with:
            'vertices': list of [x, y] coordinates.
            'edges': list of [u_index, v_index] vertex index pairs.
            'boundary': list of [patch_name, { 'type': str, 'edges': list of edge indices }].

    Returns:
        A string representing the mesh in FMS format.
    """
    output_vertices = []  # List to store the (x, y, z) coordinates of all vertices
    vertex_to_index_map = {}  # Dictionary to map (x, y, z) tuples to unique global vertex indices
    global_vertex_index = 0  # Counter for assigning unique vertex indices
    output_faces = []  # List to store the faces (triangles) of the mesh

    # Handle the case where there are no edges
    if not input_dict['edges']:
        output_str_lines = []
        output_str_lines.append(str(len(input_dict.get('boundary', []))))  # Number of patches (use .get for safety)
        output_str_lines.append("(")
        for patch_data in input_dict.get('boundary', []):  # Iterate through patch definitions
            patch_name = patch_data[0]  # Extract patch name
            patch_type = patch_data[1]['type']  # Extract patch type
            output_str_lines.append(f"{patch_name} {patch_type}")  # Add patch name and type to output
        output_str_lines.append(")")
        output_str_lines.append(f"{len(output_vertices)}( )")  # 0 vertices (empty list)
        output_str_lines.append(f"{len(output_faces)}( )")  # 0 faces (empty list)
        for _ in range(len(input_dict.get('boundary', []))):  # Add 0() for each patch (no boundaryFaces)
            output_str_lines.append("0()")
        return "\n".join(output_str_lines)  # Return the FMS string

    # Create a mapping from edge index to patch index
    edge_to_patch_map = {}
    for patch_index, patch_data in enumerate(input_dict.get('boundary', {"": {"type": None, "edges": []}}).values()):
        for edge_index in patch_data['edges']:
            edge_to_patch_map[edge_index] = patch_index

    # Iterate through each edge defined in the input
    for edge_index, edge in enumerate(input_dict['edges']):
        try:
            # Get the indices of the two vertices that make up the edge
            u_index, v_index = edge
            # Retrieve the (x, y) coordinates of the vertices from the input dictionary
            v_u = input_dict['vertices'][u_index]
            v_v = input_dict['vertices'][v_index]
        except IndexError:
            # Handle the case where a vertex index is out of range
            return "Error: Invalid vertex index in edge definition."

        # Create four vertices for the extruded edge:
        #   - Two original vertices on the z=0 plane
        #   - Two corresponding vertices extruded along the z-axis (z=0.1)
        local_vertices = [
            tuple(v_u + [0.0]),  # Add z=0.0 to the first vertex
            tuple(v_v + [0.0]),  # Add z=0.0 to the second vertex
            tuple(v_u + [0.1]),  # Add z=0.1 to the first vertex (extruded)
            tuple(v_v + [0.1]),  # Add z=0.1 to the second vertex (extruded)
        ]

        global_indices = []  # List to store the global indices of the four vertices
        # Iterate through the four vertices of the extruded edge
        for vertex_coords in local_vertices:
            # Check if this vertex (x, y, z) already exists in the vertex_to_index_map
            if vertex_coords not in vertex_to_index_map:
                # If the vertex is new:
                #   - Assign it a unique global index
                #   - Add it to the output_vertices list
                #   - Update the global_vertex_index counter
                vertex_to_index_map[vertex_coords] = global_vertex_index
                output_vertices.append(vertex_coords)
                global_vertex_index += 1
            # Add the global index of the current vertex to the global_indices list
            global_indices.append(vertex_to_index_map[vertex_coords])

        # Get the global indices of the four vertices
        v_idx_1, v_idx_2, v_idx_3, v_idx_4 = global_indices
        # Create two triangles (faces) from the four vertices:
        #   - The winding order (vertex order) is important for correct surface normals
        triangle1 = (v_idx_2, v_idx_1, v_idx_3)  # Corrected winding order
        triangle2 = (v_idx_2, v_idx_3, v_idx_4)  # Corrected winding order

        # Use the edge_to_patch_map to get the correct patch index
        patch_index = edge_to_patch_map.get(edge_index, -1)  # Default to -1 if not found
        if patch_index == -1:
            return f"Error: Edge {edge_index} is not assigned to any patch."

        # Add the two triangles to the output_faces list, along with the edge index
        output_faces.append(((triangle1[0], triangle1[1], triangle1[2]), patch_index))
        output_faces.append(((triangle2[0], triangle2[1], triangle2[2]), patch_index))

    # --- Build the FMS string ---
    output_str_lines = []  # List to store the lines of the FMS string
    output_str_lines.append(str(len(input_dict.get('boundary', []))))  # Number of patches (use .get for safety)
    output_str_lines.append("(")

    # Add boundary (patch) information to the FMS string
    for patch_data in input_dict.get('boundary', {"": {"type": None, "edges": []}}).items():  # Iterate through patch definitions
        patch_name, patch_info = patch_data  # Unpack patch name and information
        patch_type = patch_info['type']  # Get the patch type
        output_str_lines.append(f"{patch_name} {patch_type}")  # Add patch name and type to output
    output_str_lines.append(")")

    # Add vertices to the FMS string
    output_str_lines.append(f"{len(output_vertices)}( " + ' '.join([str(v).replace(',', '') for v in output_vertices]) + " )")

    # Add faces to the FMS string
    face_output_list = [
        f"(({face[0]} {face[1]} {face[2]}) {patch_index})"  # Format each face: ((v1 v2 v3) edge_index)
        for face, patch_index in output_faces
    ]
    output_str_lines.append(f"{len(output_faces)}( " + ' '.join(face_output_list) + " )")

    # Add the empty sets
    for i in range(4):
              output_str_lines.append("0()")

    return "\n".join(output_str_lines)  # Join the lines with newline characters and return the FMS string
