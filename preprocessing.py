from regularex import get_mappings, process_relationship, process_target_source

def check_brackets(s: str):
    """
    This function checks if the cypher query contains variable length relationships as those are not supposed
    to be processed by this code which marks them as 'Syntax error' if they do not make sense according to the schema

    Input: cypher query
    Output: True if variable length relationship is present, False otherwise
    """
    inside_brackets = False
    for char in s:
        if char == '[':
            inside_brackets = True
        elif char == ']':
            inside_brackets = False
        elif char == '*' and inside_brackets:
            return True
    return False

def convert_to_single_line(cypher_statement: str):
    """
    Some statments are split over multiple lines, this function converts them to a single line

    Input: cypher query
    Output: cypher query in a single line
    """
    return cypher_statement.replace("\n", " ").replace("\r", "").replace("    ", " ")

def extract_directed_statement(text: str):
    """
    This function extracts the directed statements from the cypher query

    Input: cypher query: 'MATCH (a)-[:RELATIONSHIP]->(b) RETURN a, b'
    Output: list of directed statements found inside the cypher query: ['(a)-[:RELATIONSHIP]->(b)']
    """
    # Initialize list to hold directed staments
    directed_statements = []
    # Initialize statements start and end indices
    start, end = -1, -1

    # Iterate over the text from left to right
    for i in range(len(text)):
        # Check if the character is a closing bracket
        if text[i] == ")":
            # If we're not already tracking a directed staments, find the begining of a source/target
            if start == -1:
                if i+1 < len(text) and text[i+1] in ["-", ">", "<"]:
                    # Loop backwards to find the opening bracket
                    for j in range(i, -1, -1):
                        if text[j] == "(":
                            start = j
                            break
            # If we're already tracking a staments, find the end of a source/target
            else:
                # If the next character isn't a direction indicator, this is the end of the directed part of the stament
                if i+1 == len(text) or text[i+1] not in ["-", ">", "<"]:
                    end = i+1
                    # Append the stament to the list of staments
                    directed_statements.append(text[start:end])
                    # Reset 'start' and 'end' for the next stament
                    start, end = -1, -1

    return directed_statements

def extract_relationship(directed_statements: list):
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

def get_direction_arrows(directed_statements: list):
    """
    This function extracts the direction arrows from the directed statements

    Input: list of directed statements
    Output: dictionary of direction arrows containing:
        - patterns: list of direction patterns
        - start_indices: list of start indices of direction patterns
        - found_flag: flag indicating if direction patterns were found


    Note:
    This function is not used in the final version of the code
    """
    patterns_dict = {}

    # Iterate over each directed_statement
    for i, directed_statement in enumerate(directed_statements):
        # Initialize list to hold directed patterns directions and types
        patterns = []
        # Initialize list to hold start indices of patterns
        start_indices = []
        # Flag for checking if we found a direction pattern
        found_flag = False

        # Order of patterns is important, longer patterns should be checked first
        patterns = ["-->", "<--", "->", "<-", "--", "-"]

        for pattern in patterns:
            index = directed_statement.find(pattern)
            while index != -1:
                # Only add to list if index is not within 2 of already found start_indices (to avoid overlapping patterns) the minimum distance is 2 which is empty node ()
                if not any([abs(index - idx) <= 2 for idx in start_indices]):
                    patterns.append(pattern)
                    start_indices.append(index)
                    found_flag = True
                # Continue to look for pattern after the current index + pattern length
                index = directed_statement.find(pattern, index + len(pattern))

        # Insert into the dictionary
        patterns_dict[i] = (patterns, start_indices, found_flag)

    return patterns_dict

def identify_nodes(directed_statments: list, relationship_info: dict, schema: str):
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


def split_into_substatements(statments: list):
    """
    A function that splits the complex directed_statements into sub-statements while simple ones remain the same. This process may alter the total number of nodes,
    but the number of vectors and paths remains unaltered. That's whyit can be used for accurate direction validation and standardization purposes,
    regardless of the complexity of the input Cypher query.
    
    Input: list of a single directed_statment: ['(a)-[:RELATIONSHIP]->(b)<-[:RELATIONSHIP]-(c)']
    Output: list of substatements like: ['(a)-[:RELATIONSHIP]->(b)', '(b)<-[:RELATIONSHIP]-(c)']
    """
    substatements = []

    for statment in statments:
        nodes_indices = []
        start_index = 0

        while True:
            # Find the start of the next body part
            start_index = statment.find('(', start_index)
            if start_index == -1:
                break

            # Find the end of the body part
            end_index = statment.find(')', start_index)
            if end_index == -1:
                break

            # Append the indices of the body part to nodes_indices list
            nodes_indices.append((start_index, end_index))
            # Move the start_index beyond the current body part
            start_index = end_index + 1

            # If we have two body parts, join them into a substatment
            if len(nodes_indices) == 2:
                start, end = nodes_indices[0][0], nodes_indices[1][1]
                substatment = statment[start:end + 1]
                #remove any instance of ! inside the substatment string
                substatment = substatment.replace('!', '')

                substatements.append(substatment)
                # Remove the first body part
                nodes_indices.pop(0)
    return substatements

def find_used_trios(cypher_string: str, schema_list: list):
    """
    Function that finds the used schema in the cypher_string

    Input: cypher_string, schema_list
    Output: list of used schema like: [('Person', 'ACTED_IN', 'Movie'), ('Person', 'DIRECTED', 'Movie')]
    """
    # Extract distinct node types from schema_list
    node_types = set([item for sublist in schema_list for item in sublist])
    # Identify node types present in cypher_string
    nodes_in_statement = [node for node in node_types if node in cypher_string]
    # Filter schema list
    filtered_trios = [trio for trio in schema_list if 
                      (trio[0] in nodes_in_statement and trio[2] in nodes_in_statement
                      and nodes_in_statement.index(trio[0]) != nodes_in_statement.index(trio[2])) or 
                      (trio[0] in nodes_in_statement and trio[1] in nodes_in_statement) or 
                      (trio[1] in nodes_in_statement and trio[2] in nodes_in_statement)
    ]
    return filtered_trios

def extract_schema(schema_str: str):
    """
    Extracts the schema as a list from the schema tuple string

    Input: schema_str
    Output: list of schema like: [('Person', 'ACTED_IN', 'Movie'), ('Person', 'DIRECTED', 'Movie')]
    """
    schema_str = schema_str.strip('()')
    schemas = schema_str.split('), (')
    schema_list = []
    schema_list.clear()
    for schema in schemas:
        nodes = schema.split(', ')
        schema_list.append((nodes[0], nodes[1], nodes[2]))
    return schema_list

def process_strings(input_list: list):
    """
    Function that processes the strings in the input_list to remove any data before : in the relationship node
    
    Input: list of strings
    Output: list of processed strings
    """
    processed_list = []
    for string in input_list:
        inside_brackets = False
        processed_string = ''
        for char in string:
            if char == '[':
                inside_brackets = True
                bracket_content = ''
            elif char == ']':
                inside_brackets = False
                if ':' in bracket_content:
                    bracket_content = bracket_content.split(':')[1]
                processed_string += '[' + bracket_content + ']'
            elif inside_brackets:
                bracket_content += char
            else:
                processed_string += char
        processed_list.append(processed_string)
    
    return processed_list

def remove_brackets(input_string: str):
    """
    Function that removes the brackets from the input_string if the relationship node is empty like []

    Input: input_string like: '(a)-[:]->(b)'
    Output: processed_string like: '(a)-->(b)'
    """
    #Used to standardzie strings without relationship node
    inside_brackets = False
    processed_string = ''
    for char in input_string:
        if char == '[':
            inside_brackets = True
        elif char == ']':
            inside_brackets = False
        elif not inside_brackets:
            processed_string += char
    
    return processed_string

def check_syntax(cypher_substring: str, schema: list):
    """
    Function that evaluates if the cypher_substring is syntactically correct according to the schema, this function also marks variable length relationships as syntactically incorrect,
    thats why we need to raise the variable relationship flag before calling this function.
    
    Input: cypher_substring, schema
    Output: True if syntactically correct, False otherwise
    """
    # Extract elements from the cypher substring
    cypher_elements = cypher_substring[1:-1].split("-") 
    try:
        # Determine direction of relationship
        if '>' in cypher_elements[2]:
            cypher_source = cypher_elements[0].split(":")[1] 
            cypher_rel = cypher_elements[1][1:-1] 
            cypher_target = cypher_elements[2].split(":")[1]
        elif '<' in cypher_elements[0]:
            cypher_source = cypher_elements[2].split(":")[1]
            cypher_rel = cypher_elements[1][1:-1] 
            cypher_target = cypher_elements[0].split(":")[1] 
        else:
            #Error handling if we're still unable to identify the relationship node while it isn't empty, we can still check the direction if source and target nodes are present
            #nodes are unidentified because we do not know what nodes are used since identify_nodes function needs relationship info which we do not have here
            unidentified_node1 = cypher_elements[0].split(":")[1]
            cypher_rel = cypher_elements[1][1:-1]
            unidentified_node2 = cypher_elements[2].split(":")[1]
            for schema_element in schema:
                schema_source, schema_rel, schema_target = schema_element
                if (schema_source in unidentified_node1 and 
                    schema_rel in cypher_rel and 
                    schema_target in unidentified_node2) or (schema_source in unidentified_node2 and 
                    schema_rel in cypher_rel and 
                    schema_target in unidentified_node1):
                    return True 
            try:
                if cypher_rel == '':
                    return True
            except UnboundLocalError:
                return True
            return False
    except IndexError:
        return True
    try:
        if cypher_rel == '':
            return True
    except UnboundLocalError:
        return True
    for schema_element in schema:
        schema_source, schema_rel, schema_target = schema_element
        if (schema_source in cypher_source and 
            schema_rel in cypher_rel and 
            schema_target in cypher_target):
            return True 

    return False

def validate_direction(substatements: list, relationship_dict: dict, schema: str, identified_nodes: dict):
    """
    Function that validates the direction of the relationships in the substatements

    Input: substatements, relationship_dict, schema, identified_nodes
    Output: list of substatements with corrected direction
    """

    final_statments = []
    # Extract the schemas as a list for easier processing
    schemalist = extract_schema(schema)
    # Standardize the strings
    substatements = process_strings(substatements)
    # Iterate over each substatment
    for i, substatment in enumerate(substatements):
        # Find the used schema in the substatment
        used_schema = find_used_trios(substatment, schemalist)
        # if relationship info status is True and the nodes are identified 
        if relationship_dict[i][2] and bool(identified_nodes[i]):
            for schema in used_schema:
                # Find the position of "->" or "<-" symbol
                arrow_forward_position = substatment.find("-[{}]->".format(schema[1]))
                arrow_backward_position = substatment.find("<-[{}]-".format(schema[1]))
                source_position = substatment.find(schema[0])
                relation_position = substatment.find(schema[1])
                target_position = substatment.find(schema[2])
                if source_position == -1:
                    if target_position > relation_position and arrow_backward_position != -1 and arrow_forward_position ==-1:
                        substatment = substatment.replace(f"<-[{schema[1]}]-", f"-[{schema[1]}]->")
                    elif target_position < relation_position and arrow_backward_position == -1 and arrow_forward_position !=-1:
                        substatment = substatment.replace(f"-[{schema[1]}]->", f"<-[{schema[1]}]-")
                elif target_position == -1:
                    if source_position > relation_position and arrow_backward_position == -1 and arrow_forward_position !=-1:
                        substatment = substatment.replace(f"-[{schema[1]}]->", f"<-[{schema[1]}]-")
                    elif source_position < relation_position and arrow_backward_position != -1 and arrow_forward_position ==-1:
                        substatment = substatment.replace(f"<-[{schema[1]}]-", f"-[{schema[1]}]->")
                elif source_position == -1 and target_position == -1:
                    continue
                elif source_position != -1 and target_position != -1:
                    if source_position > target_position and arrow_backward_position == -1 and arrow_forward_position !=-1:
                        substatment = substatment.replace(f"-[{schema[1]}]->", f"<-[{schema[1]}]-")
                    elif source_position < target_position and arrow_backward_position != -1 and arrow_forward_position ==-1:
                        substatment = substatment.replace(f"<-[{schema[1]}]-", f"-[{schema[1]}]->")

            final_statments.append(substatment)
        else:
            # Remove the brackets from the substatment, if present, when the relationship node is not identified
            substatment = remove_brackets(substatment)
            for schema in used_schema:
                # Find the position of "->" or "<-" symbol
                arrow_forward_position = substatment.find("-->".format(schema[1]))
                arrow_backward_position = substatment.find("<--".format(schema[1]))
                source_position = substatment.find(schema[0])
                target_position = substatment.find(schema[2])
                if target_position > source_position and arrow_backward_position != -1 and arrow_forward_position ==-1:
                    substatment = substatment.replace("<--", "-->")
                elif target_position < source_position and arrow_backward_position == -1 and arrow_forward_position !=-1:
                     substatment = substatment.replace("-->", "<--")
                elif (source_position == -1 and target_position == -1)  or (arrow_backward_position ==-1 and arrow_forward_position !=-1):
                    continue
            final_statments.append(substatment)

    return final_statments

def prepare_string(row: list):
    """
    Main function that prepares and processes the string for the extraction of the vectors

    Input: row from the dataframe
    Output: list of processed strings
    """
    statement = convert_to_single_line(row[0])
    statement = get_mappings(statement, row[1])

    # Extract the relevant part containing vectors
    directed_statment = extract_directed_statement(statement)

    # Check to see if the statement contains variable length relationships if it does, return the original statement
    variable_length_flag = check_brackets(statement)
    if variable_length_flag:
        return statement, variable_length_flag
    
    # Preprocess nodes to not contain unrelevant data
    for i in range(len(directed_statment)):
        directed_statment[i] = process_relationship(directed_statment[i], row[1])
        directed_statment[i] = process_target_source(directed_statment[i], row[1])

    # Split the directed_statment into substatements
    substatements= split_into_substatements(directed_statment)

    # Get the node info from the substatements
    relationship_info = extract_relationship(substatements)
    nodes = identify_nodes(substatements, relationship_info, row[1])

    # Validate the direction of the relationships in the substatements
    directed_statment = validate_direction(substatements, relationship_info, row[1], nodes)

    # Check the syntax of the substatements before returning them
    output = [None] * len(directed_statment)
    for i in range(len(directed_statment)):
        schema = extract_schema(row[1])
        used_schema = find_used_trios(substatements[i], schema)
        if check_syntax(directed_statment[i], used_schema):
            output[i] = directed_statment[i]
        else:
            output[i] = 'Syntax error'            

    return output, variable_length_flag
