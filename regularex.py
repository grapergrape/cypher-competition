import re 

""" 
This file contains functions that are used to process the cypher queries to be more similar to the schema
I tried to use as little regex as possible for this competition, even though I could completly avoid it
I still used some, in the future I would like to rewrite this file to not use regex at all
"""
def get_mappings(query: str, schema: str):
    """
    This function gets the mappings between the query and the schema like, converts all the nodes in the query to be like those in schema if possible
    
    Input: query, schema
    Output: query with nodes mapped to schema    
    """

    # Extract nodes from schema
    schema_nodes = re.findall(r'\((.*?)\)', schema)
    schema_dict = {}
    for node in schema_nodes:
        node_parts = node.split(',')
        label = node_parts[0].strip()
        relationship = node_parts[1].strip()
        
        if label in schema_dict:
            schema_dict[label].append(relationship)
        else:
            schema_dict[label] = [relationship]


    # Extract nodes from query
    query_nodes = re.findall(r'\((.*?)\)', query)
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

def infer_labels_from_schema(query: str, schema_dict: dict):
    """
    This function infers the labels of nodes in the query that are not specified in the query
    like () or (a) or by looking at the schema and converting them to (a:Person) or (a:Person:Actor)

    Input: query, schema_dict
    Output: query with inferred labels
    """
    for node in re.finditer(r'\((.*?)\)', query):
        node_name = node.group(1)
        if node_name == '*' or node_name == ' ':
            continue
        if ':' not in node_name:
            if node_name in schema_dict:
                query = query.replace(f'({node_name})', f'({node_name}:{schema_dict[node_name]})')
            else:
                continue
    return query


def process_relationship(cypher: str, schema: str):
    """
    This function processes the relationships in the cypher query to be more similar to the schema, removes abnormalities
    If there is multiple relationships between two nodes, it will only keep the first one, 
    since two relationships between two same nodes should always have same 

    Input: cypher query, schema
    Output: cypher query with relationships processed
    """

    # Extract triples (source_node, relation, target_node) from schema
    triples = re.findall(r'\(([^,]+), ([^,]+), ([^)]+)\)', schema)

    for triple in triples:
        source_node, relation, target_node = triple

        # Construct the regex pattern for the relationship with properties
        relation_pattern = re.escape('[') + r'?`?' + re.escape(relation) + r'`?' + r'[^]]*?' + re.escape(']')

        # Replace relationship nodes with properties with just the relationship
        cypher = re.sub(relation_pattern, f'{relation}]', cypher)

    return cypher

def process_target_source(cypher: str, schema: str):
    """
    This function processes the target and source nodes in the cypher query to be more similar to the schema


    Input: cypher query, schema
    Output: cypher query with target and source nodes processed
    """
    # Extract triples (source_node, relation, target_node) from schema
    triples = re.findall(r'\(([^,]+), ([^,]+), ([^)]+)\)', schema)

    for triple in triples:
        source_node, relation, target_node = triple

        # Construct the regex pattern for source and target nodes with properties
        source_pattern = re.escape('(') + r'?`?' + re.escape(source_node) + r'`?' + r'[^)]*?' + re.escape(')')
        target_pattern = re.escape('(') + r'?`?' + re.escape(target_node) + r'`?' + r'[^)]*?' + re.escape(')')

        # Replace source nodes with properties with just the node label
        cypher = re.sub(source_pattern, f'({source_node})', cypher)

        # Replace target nodes with properties with just the node label
        cypher = re.sub(target_pattern, f'({target_node})', cypher)

    return cypher
