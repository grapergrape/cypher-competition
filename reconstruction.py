def symbol_extractor(stringlist: list):
    """
    This function extracts the symbols resembling vectors from the input stringlist and returns them as a list

    Input: stringlist
    Output: list of symbols like ['->', '<-', '-']
    """
    symbols = []
    if stringlist == ['Syntax error']:
        return ['Syntax error']
    for string in stringlist:
        i = 0
        while i < len(string):
            if string[i:i+2] in ('->', '<-'):
                symbols.append(string[i:i+2])
                i += 2
            elif string[i] == '-':
                symbols.append(string[i])
                i += 1
            else:
                i += 1
    return symbols

def symbol_inserter(target_string: str, input_sequence: list):
    """
    This function inserts the symbols from input_sequence into the target_string
    
    Input: target_string, input_sequence
    Output: output string with inserted sequence
    """
    output = ''
    input_index = 0
    skip_next = False
    for i in range(len(target_string)):
        if skip_next:
            skip_next = False
            continue
        if i < len(target_string) - 1 and target_string[i:i+2] in ['->', '<-']:
            output += input_sequence[input_index]
            input_index += 1
            skip_next = True
        elif target_string[i] == '-':
            output += input_sequence[input_index]
            input_index += 1
        else:
            output += target_string[i]
    return output



def solver(stringlist: list, target_string: str):
    """
    This is the main function from this helper module that takes the input stringlist and the target string and returns the output string
    
    Input: stringlist, target_string
    Output: output string
    """ 
    input_sequence = symbol_extractor(stringlist)
    
    if 'Syntax error' in input_sequence:
        return 'Syntax error'
    
    output = symbol_inserter(target_string, input_sequence)
    return output
