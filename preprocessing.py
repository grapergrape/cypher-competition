from dicts import extract_relationship, identify_nodes

def check_brackets(s: str) -> bool:
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

def convert_to_single_line(cypher_statement: str) -> str:
    """
    Some statments are split over multiple lines, this function converts them to a single line

    Input: cypher query
    Output: cypher query in a single line
    """
    return cypher_statement.replace("\n", " ").replace("\r", "").replace("    ", " ")

def infer_labels_from_schema(query: str, schema_dict: dict) -> str:
    """
    This function infers the labels of nodes in the query that are not specified in the query
    like () or (a) or by looking at the schema and converting them to (a:Person) or (a:Person:Actor)

    Input: query, schema_dict
    Output: query with inferred labels
    """
    start = 0
    while True:
        start = query.find('(', start)
        if start == -1: break
        end = query.find(')', start)
        if end == -1: break
        node_name = query[start+1:end].strip()
        
        if node_name == '*' or node_name == '':
            start = end + 1
            continue

        if ':' not in node_name:
            if node_name in schema_dict:
                query = query[:start] + f'({node_name}:{schema_dict[node_name]})' + query[end+1:]
        start = end + 1
        
    return query

def get_mappings(query: str, schema: str) -> str:
    """
    This function gets the mappings between the query and the schema like, converts all the nodes in the query to be like those in schema if possible
    
    Input: query, schema
    Output: query with nodes mapped to schema    
    """
    # Extract nodes from schema
    schema_nodes=[part.strip() for part in schema.replace('(', '').replace(')', '').split(',')]
    schema_dict = {}
    for i in range(0, len(schema_nodes), 3):
        label = schema_nodes[i].strip()
        relationship = schema_nodes[i+1].strip()
        
        if label in schema_dict:
            schema_dict[label].append(relationship)
        else:
            schema_dict[label] = [relationship]

    # Extract nodes from query
    start = 0
    query_nodes = []
    while True:
        start = query.find('(', start)
        if start == -1: break
        end = query.find(')', start)
        if end == -1: break
        node = query[start+1:end].strip()
        query_nodes.append(node)
        start = end+1

    query_nodes_dict = {node.split(':')[0]: node for node in query_nodes if ':' in node}

    # Iterate through the query nodes and update the query
    for node in query_nodes:
        if node == '*' or node == ' ':
            continue

        if ':' in node:
            continue

        # Check if the node is in schema_dict
        if node in schema_dict:
            query = query.replace(f'({node})', f'({node}:{schema_dict[node]})')
        else:
            # Check if there's a mapping in query_nodes_dict
            if node in query_nodes_dict:
                query = query.replace(f'({node})', f'({query_nodes_dict[node]})')
            else:
                # If not, raise an error
                continue

    # Handle nodes like () by inferring labels from the schema
    query = infer_labels_from_schema(query, schema_dict)

    return query


def process_relationship(cypher: str, schema: str) -> str | list[tuple[str, str, str]]:
    """
    This function processes the relationships in the cypher query to be more similar to the schema, removes abnormalities
    If there is multiple relationships between two nodes, it will only keep the first one, 
    since two relationships between two same nodes should always have same 

    Input: cypher query, schema
    Output: cypher query with relationships processed
    """
    # Split the schema by "), (" to get a list of raw triples
    raw_triples = schema.strip("()").split("), (")

    # For each raw triple, split by ", " to get the nodes and relationship
    triples = [triple.split(", ") for triple in raw_triples if triple.strip()]

    # Initialize a processed cypher string
    processed_cypher = ""

    # Initialize a flag to denote if we're currently processing a relationship
    processing_relationship = False

    # Iterate through the characters of the cypher string
    for char in cypher:
        if char == '[':
            processing_relationship = True
            relationship = ""
        
        if processing_relationship:
            relationship += char

        if char == ']':
            processing_relationship = False

            # Check if the found relationship matches a relationship in the schema, if yes, replace it
            for triple in triples:
                source_node, relation, target_node = [t.strip(' `') for t in triple]
                if relation in relationship:
                    relationship = f'[{relation}]'
                    break

            processed_cypher += relationship
        elif not processing_relationship:
            processed_cypher += char

    return processed_cypher, triples

def process_target_source(cypher: str, triples: list) -> str:
    """
    This function processes the target and source nodes in the cypher query to be more similar to the schema


    Input: cypher query, schema
    Output: cypher query with target and source nodes processed
    """

    for triple in triples:
        source_node, relation, target_node = [t.strip(' `') for t in triple]

        # Lists to hold our cypher fragments
        cypher_fragments = []
        last_index = 0

        # Find the next ( or ) starting at the given index
        for index in range(len(cypher)):
            if cypher[index] in ['(', ')']:
                # Append the cypher fragment to our list
                cypher_fragments.append(cypher[last_index:index+1])
                last_index = index + 1

        # Process the cypher fragments
        for index, fragment in enumerate(cypher_fragments):
            # If fragment starts with source_node or target_node, replace it
            if fragment.lstrip('(`').startswith(source_node):
                cypher_fragments[index] = f'({source_node})'
            elif fragment.lstrip('(`').startswith(target_node):
                cypher_fragments[index] = f'({target_node})'

        # Join the processed fragments back into the cypher string
        cypher = ''.join(cypher_fragments)

    return cypher

def extract_directed_statement(text: str) -> list[str]:
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

def split_into_substatements(statments: list) -> list[str]:
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

def find_used_trios(cypher_string: str, schema_list: list) -> list[tuple[str, str, str]]:
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

def process_strings(input_list: list) -> list[str]:
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

def remove_brackets(input_string: str) -> str:
    """
    Function that removes the brackets from the input_string if the relationship node contains no relevant data

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

def check_syntax(cypher_substring: str, schema: list) -> bool:
    """
    Function that evaluates if the cypher_substring is syntactically correct according to the schema, 
    this function also marks variable length relationships as syntactically incorrect,
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

def validate_direction(substatements: list, relationship_dict: dict, schema: str, identified_nodes: dict) -> list[str] | list[tuple[str, str, str]]:
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
                # Find the position of the source and target nodes
                source_position = substatment.find(schema[0])
                relation_position = substatment.find(schema[1])
                target_position = substatment.find(schema[2])
                # Logic if the source is not present 
                if source_position == -1:
                    if target_position > relation_position and arrow_backward_position != -1 and arrow_forward_position ==-1:
                        substatment = substatment.replace(f"<-[{schema[1]}]-", f"-[{schema[1]}]->")
                    elif target_position < relation_position and arrow_backward_position == -1 and arrow_forward_position !=-1:
                        substatment = substatment.replace(f"-[{schema[1]}]->", f"<-[{schema[1]}]-")
                # Logic if the target is not present
                elif target_position == -1:
                    if source_position > relation_position and arrow_backward_position == -1 and arrow_forward_position !=-1:
                        substatment = substatment.replace(f"-[{schema[1]}]->", f"<-[{schema[1]}]-")
                    elif source_position < relation_position and arrow_backward_position != -1 and arrow_forward_position ==-1:
                        substatment = substatment.replace(f"<-[{schema[1]}]-", f"-[{schema[1]}]->")
                # If neither source nor target is present, we return the original substatment
                # If a node is defined but uses a weird marking it should've been correct in get_mappings function
                elif source_position == -1 and target_position == -1:
                    continue
                # Logic if both source and target are present
                elif source_position != -1 and target_position != -1:
                    if source_position > target_position and arrow_backward_position == -1 and arrow_forward_position !=-1:
                        substatment = substatment.replace(f"-[{schema[1]}]->", f"<-[{schema[1]}]-")
                    elif source_position < target_position and arrow_backward_position != -1 and arrow_forward_position ==-1:
                        substatment = substatment.replace(f"<-[{schema[1]}]-", f"-[{schema[1]}]->")

            final_statments.append(substatment)
        else:
            # The relationship node is not present
            # Remove the brackets from the substatment, if present, when the relationship node is not identified
            substatment = remove_brackets(substatment)
            for schema in used_schema:
                # Find the position of "->" or "<-" symbol
                arrow_forward_position = substatment.find("-->".format(schema[1]))
                arrow_backward_position = substatment.find("<--".format(schema[1]))
                source_position = substatment.find(schema[0])
                target_position = substatment.find(schema[2])

                # Same logic as above, but without the relationship node
                if target_position > source_position and arrow_backward_position != -1 and arrow_forward_position ==-1:
                    substatment = substatment.replace("<--", "-->")
                elif target_position < source_position and arrow_backward_position == -1 and arrow_forward_position !=-1:
                     substatment = substatment.replace("-->", "<--")
                elif (source_position == -1 and target_position == -1)  or (arrow_backward_position ==-1 and arrow_forward_position !=-1):
                    continue
            final_statments.append(substatment)

    return final_statments, schemalist

def prepare_string(row: list) -> tuple[list[str], bool]:
    """
    Main function that prepares and processes the string for the extraction of the vectors

    Input: row from the dataframe
    Output: list of processed strings
    """
    # Get the mappings between the unknown nodes in query and the schema, for example this converts nodes like (a) to (a:Person)
    statement = get_mappings(convert_to_single_line(row[0]), row[1])

    # Extract the relevant part containing vectors
    directed_statment = extract_directed_statement(statement)

    # Check to see if the statement contains variable length relationships if it does, return the original statement
    variable_length_flag = check_brackets(statement)
    if variable_length_flag:
        return statement, variable_length_flag
    
    # Preprocess nodes to not contain unrelevant data
    for i in range(len(directed_statment)):
        directed_statment[i],triples = process_relationship(directed_statment[i], row[1])
        directed_statment[i] = process_target_source(directed_statment[i], triples)

    # Split the directed_statment into substatements
    substatements= split_into_substatements(directed_statment)

    # Get the node info from the substatements, 
    # relationship info is a dict but in the final  version only the bool value is used

    relationship_info = extract_relationship(substatements)
    nodes = identify_nodes(substatements, relationship_info, row[1])

    # Validate the direction of the relationships in the substatements
    directed_statment , schema = validate_direction(substatements, relationship_info, row[1], nodes)

    # Check the syntax of the substatements before returning them
    output = [None] * len(directed_statment)
    for i in range(len(directed_statment)):
        used_schema = find_used_trios(substatements[i], schema)
        if check_syntax(directed_statment[i], used_schema):
            output[i] = directed_statment[i]
        else:
            output[i] = 'Syntax error'            

    return output, variable_length_flag
