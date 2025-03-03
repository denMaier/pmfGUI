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
    for patch_index, patch_data in enumerate(input_dict.get('boundary', [])):
        _, patch_info = patch_data
        for edge_index in patch_info['edges']:
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
    for patch_data in input_dict.get('boundary', []):  # Iterate through patch definitions
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

    #return "\n".join(output_str_lines)  # Join the lines with newline characters and return the FMS string
    with open("test.out", 'w') as f:
        print("Lets output")
        f.write('\n'.join(output_str_lines))

# Example usage:
data = {
    'vertices': [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
    'edges': [[0, 1], [1, 2], [2, 3], [3, 0]],
    'boundary': [
        ('inlet', {'type': 'patch', 'edges': [0]}),
        ('outlet', {'type': 'patch', 'edges': [2]}),
        ('wall1', {'type': 'wall', 'edges': [1, 3]})#,
        #('wall2', {'type': 'wall', 'edges': [3]})
    ]
}

edgesToFMS(data)
