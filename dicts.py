def extract_relationship(directed_statements: list) -> dict[int, tuple[list[str], list[int], bool]] :
    """
    This function extracts the relationship info from the directed statements

    Input: list of directed statements
    Output: dictionary of relationship info containing:
        - info: list of relationship info
        - start_indices: list of start indices of relationship info
        - found_flag: flag indicating if relationship info was found
    """
    info_dict = {}

    # Iterate over each directed statement
    for i, directed_statement in enumerate(directed_statements):
        # Initialize list to hold info from this directed_statement's relationships
        info = []
        # Initialize list to hold start indices of directed_statements
        start_indices = []
        # Flag for checking if we found a meaningful relationship node
        found_flag = False
        # Split the directed_statement on "-"
        parts = directed_statement.split("-")

        # Iterate over each part
        for part in parts:
            # Check if the part has a relationship node (inside square brackets)
            if "[" in part and "]" in part:
                # Store starting index of the relationship node
                start_indices.append(directed_statement.index(part))
                # Extract relationship info
                relationship = part[part.index('[')+1: part.index(']')]
                # Check if relationship info is not "*" and not empty
                if relationship != "*" and relationship != "":
                    # Remove ":" from the relationship info if it exists
                    if ":" in relationship:
                        relationship = relationship.split(":", 1)[1]
                    info.append(relationship)
                    found_flag = True

        # Insert into the dictionary
        info_dict[i] = (info, start_indices, found_flag)

    return info_dict

def identify_nodes(directed_statments: list, relationship_info: dict, schema: str) -> dict[int, dict[str, dict]]:
    """
    Function that identifies the nodes in the directed_statments and returns them in a dictionary, only works if 
    relationship node is present

    Input: list of directed_statments, relationship_info, schema
    Output: dictionary of identified nodes containing:
        - source: dictionary of source nodes
        - target: dictionary of target nodes
    """
    # Convert schema string to list of tuples
    schema = [tuple(item.split(", ")) for item in schema.strip("()").split("), (")]
    nodes_dict = {}

    # Iterate over each directed_statment
    for i, directed_statment in enumerate(directed_statments):
        # Check if the relationship_info status for this directed_statment is True
        if relationship_info[i][2]:
            # Get relationship info in this directed_statment
            directed_statment_relationship_info = relationship_info[i][0][0]

            # If the directed_statment_relationship_info info starts with "!", remove it
            if directed_statment_relationship_info.startswith("!"):
                directed_statment_relationship_info = directed_statment_relationship_info[1:]

            # Create sub-schema
            sub_schema = [item for item in schema if item[1] == directed_statment_relationship_info]

            nodes_dict[i] = {}  # Initialize the dict for this directed_statment

            # Check which source/target body parts from the sub-schema are present in the directed_statment
            for item in sub_schema:
                # Check for the body parts in the directed_statment
                for idx, body_part in enumerate([item[0], item[2]]):
                    start_index = directed_statment.find(body_part)
                    if start_index != -1:
                        part_type = 'source' if idx == 0 else 'target'
                        # save info in separate keys for 'source' and 'target'
                        nodes_dict[i][part_type] = {"directed_statment": i, "part": part_type, "name": body_part, "start_index": start_index, "schema_item": item}
    
    return nodes_dict