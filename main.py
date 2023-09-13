import csv
from reconstruction import solver
from preprocessing import convert_to_single_line, prepare_string

def main(csv_path: str, row_number: int):
    """
    Main function that loads the desired line form csv file and 
    calls the main processing function on it and then compares the output to the correct anwser

    Input: csv_path, row_number
    Output: None
    """
    with open(csv_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        for i in range(row_number):
            next(csv_reader)
        row = next(csv_reader)

        #Call main processing funciton on input cypher statemenet
        output, variable_length_flag = prepare_string(row)

        #Check if the input statement is of variable length (contains *)
        if not variable_length_flag:
            solution = solver(output, f'''{convert_to_single_line(row[0])}''')
        else:
            #When variable length is present, the output should just match the input statement
            solution = output
        print("Input statement:")
        print(convert_to_single_line(row[0]))
        print("------------------------------")
        print("My output:")
        print(solution)
        if row[2] == '':
            #Some rows were marked as incorrect syntax by Tomaz and were left empty
            #Since my code marks lines with incorrect syntax as 'Syntax error', I will compare it to that
            correct_anwser = 'Syntax error'
        else:
           correct_anwser = convert_to_single_line(row[2])
        print('------------------------------')
        print('Correct input anwser:')
        print(correct_anwser)
        #Compare the output of my code to the correct anwser from csv file
        if solution == correct_anwser:
            print('Evaluation: Correct')
            return True
        elif solution == 'Syntax error':
            print('My code marks this input statement as invalid (syntax error)')
        else:
            print('Evaluation: Incorrect')
            return False
if __name__ == '__main__':
    final_evaluation = []   
    for i in range(74):
        print("===============================================================================")
        print("Statement number: ", i)
        final_evaluation.append(main('examples.csv', i))
    print("===============================================================================")
    print("Final evaluation:")
    if all(final_evaluation):
        print("All correct")
    else:
        print("Fail")
