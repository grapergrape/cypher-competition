
# Cypher Competition Solution

This repository contains my solution for the Cypher competition.

## Author
Gašper Škornik

## Description

The solution consists of several Python scripts that are used to pre-process the data, execute the main program, and reconstruct the results. The program reads a CSV file, processes the Cypher queries, and outputs the results. It works by extracting just the part of the cypher query that is directed, then it validates the direction of that part based on schema, extracts the vectors and paths from the corrected sub query and inserts them into the original query.

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

The script also automatically validates the output and it's overall performance.

## Scripts

- `preprocessing.py`: This helper script is used for pre-processing the data. It reads the input CSV file and prepares the data for further processing.

- `main.py`: This is the main script that executes the program. It processes the Cypher queries and outputs the results.

- `reconstruction.py`: This helper script is used to reconstruct the results. It takes the output from the main script and reconstructs the results in a more readable format.

## Usage

To run the solution, execute the `main.py` script. The script reads the input data from a CSV file named `examples.csv`.

Please ensure that the required input file `examples.csv` is present in the same directory as the scripts.

## License

Original Licence provided from the competition author
