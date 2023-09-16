# Cypher Competition Solution

This repository contains my regex-less, raw parsing of input statments solution for the Cypher competition.

## Author
Gašper Škornik

## Description

This code consists of several Python scripts that are used to pre-process the data, execute the main program, and reconstruct the results. It reads a CSV file, processes the Cypher queries, and outputs the results. It works by extracting just the part of the cypher query that is directed, then it validates the direction of that part based on schema, extracts the vectors and paths from the corrected sub query and inserts them into the original query.

Upon realizing that the number of lines is a part of the competition's evaluation criteria, I decided to go all in on regex-less vector validation, especially given the likely excess of lines already present.

## Flow

Input:
MATCH (a:Person:Actor)<-[:ACTED_IN]-(:Movie) RETURN a, count(*)

Preprocessed into: 
(a:Person:Actor)<-[:ACTED_IN]-(:Movie)

Validated or corrected based on schema: 
(a:Person:Actor)-[:ACTED_IN]->(:Movie)

Extracted sequence:
['-','->']

Output after insertion of sequence:
MATCH (a:Person:Actor)-[:ACTED_IN]->(:Movie) RETURN a, count(*)

The script suite also includes automated validation of output and gauging of overall performance.

## Scripts

- `preprocessing.py`: This helper script is used for pre-processing the data. It reads the input CSV file and prepares the data for further processing.

- `main.py`: This is the main script that executes the program. It processes the Cypher queries and outputs the results.

- `reconstruction.py`: This helper script is used to reconstruct the results. It takes the output from the main script and reconstructs the results in a more readable format.

- `dicts.py`: This auxiliary script is utilized to store pertinent information about source/target nodes and relationship nodes in organized dictionaries.

## Usage

To run the solution, execute the `main.py` script. The script reads the input data from a CSV file named `examples.csv`.

Please ensure that the required input file `examples.csv` is present in the same directory as the scripts.

## License

The original license is provided by the competition author and is present within the repo.
