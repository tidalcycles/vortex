#########################################################################
# Vortex mini-notation parser
# base python implementation -- no grammars or abstract syntax trees.
#
# First check for correct pairing of brackets.
# Then remove non-informative whitespace and standardize the formatting.
# Then handle brackets -- calculate depth of nested-ness 
# and special care is needed for modifiers of brackets like 
#    '[hh hh]@3', '<bd hh>*3', '[bd](3,8)'.
# '(' and it's closing bracket i call 'bracket modifiers'
#
# parse the contents recursively from least-nested
# to most-nested for ',' , '.', ' ', '_', '|', etc to
# decide which functions to call to reconstruct the pattern..
#########################################################################
import re
import utils
import time

# define symbols for mini-notation
brackets = {'[' : ']', '{' : '}', '<' : '>'}
# normal meaning 'non-modifier' brackets
all_normal_brackets = utils.concat(brackets.items())

# a type of brace used for euclidean rhythms, 
# and only used as modifiers of other elements.
modifier_brackets = {'(' : ')'}

normal_left_braces = brackets.keys()
normal_right_braces = brackets.values()


all_bracket_matches = {v : k for k,v in {**brackets, **modifier_brackets}.items()}
all_brackets = utils.concat(all_bracket_matches.items())
left_braces = all_bracket_matches.values()
right_braces = all_bracket_matches.keys()



# modifiers that don't take an argument
# may operate on brackets
nullary_modifiers = ['?']
# in tidal, `s "bd hh?"` is the same as `s "bd hh    ?"`
# but `s "bd hh hh?"` is not the same as `s "bd hh hh    ?"`
# i think this second case is a bug so i'm removing the white space before. 

# these modifiers necessarily take an argument on the right.
# may operate on brackets.
argument_modifiers = ['*', '/', '@', '!', '%',':'] # ':' isn't j
# some of these (only '@', '!', '?') can these be applied to euclidean rhythms e.g. bd(3,8)@4

# everything that initiates a modifier.
all_modifier_inits = list(modifier_brackets.keys()) + argument_modifiers + nullary_modifiers 

# whitespace between '*' and '/' and their argument
#  results in an error.
# but only in `s "bd "` type strings, not in `# gain`, for example.

# reserved symbols can't be used in variable names, they get parsed.
# they are whitespace agnostic, won't affect brackets.
# '~' adds a subdivision,
# so the space parser will need to be aware of '~'
reserved_symbols = ['|', '~', ',']

# can be used in variable names but if flanked by white space they get parsed
symbols_allowed_in_variables = ['_', '.']


# combine all symbols that are ok to remove flanking whitespace from.  
whitespace_agnostic_symbols = all_normal_brackets +          \
                              utils.concat(modifier_brackets.items()) + \
                               argument_modifiers + reserved_symbols

def check_bracket_syntax(mini_notation):
    """ 
    Makes sure brackets are correctly matched and closed,
    otherwise a descriptive SyntaxError is raised.
    """
    bracket_stack = []
    for pos, c in enumerate(mini_notation):
        if c in left_braces:
            bracket_stack.append(c)
        elif c in right_braces:
            left_match = all_bracket_matches[c]
            if ((len(bracket_stack) > 0) and (left_match == bracket_stack[-1])):
                bracket_stack.pop()
            else:
                # TODO:  implement printing '^' with whitespace to point to exact error.
                raise SyntaxError(f'Closing brace {c} not matched with opening brace.')
        # make sure commas occur inside brackets.
        elif c == ',':
            if len(bracket_stack) == 0:
                raise SyntaxError(f'\",\" found outside of brackets.')
    if len(bracket_stack) != 0:
        if len(bracket_stack) == 1:
            raise SyntaxError(f'Bracket {bracket_stack[0]} is not properly closed.')
        else:
            raise SyntaxError(f'Brackets {" ".join(bracket_stack)} are not properly closed.')


def remove_extra_whitespace(mini_notation : str) -> str:
    """
    Tidies up strings for parsing by removing extraneous white space.
    """

    for s_i, symbol in enumerate(whitespace_agnostic_symbols):
        e_symbol = '\\' + symbol
        if symbol in all_normal_brackets:
            # fix ] ] -> ]] for cases like [hh [hh hh] ]
            mini_notation = re.sub(r'{}[\s]*{}'.format(e_symbol, e_symbol), f'{symbol} {symbol}',mini_notation)
        # remove trailing whitespace from left and leading whitespace from right brackets.    
        if symbol in normal_left_braces:
            mini_notation = re.sub(r'{}[\s]*'.format(e_symbol), f'{symbol}', mini_notation)
        elif symbol in normal_right_braces:
            mini_notation = re.sub(r'[\s]*{}'.format(e_symbol), f'{symbol}', mini_notation)
        # remove all whitespace
        else:
            mini_notation = re.sub(r'[\s]*{}[\s]*'.format(e_symbol), f'{symbol}', mini_notation)
            #mini_notation = mini_notation.replace(symbol + " ", symbol)
            #mini_notation = mini_notation.replace(" " + symbol,  symbol)
            
    # remove leading whitespace from nullary modifiers (only '?' currently)   
    for symbol in nullary_modifiers:
        mini_notation = mini_notation.replace(" " + symbol, symbol)

    # for debugging the whitespace insertion step of parsing.  
    # TODO:  add to logger.
    #print(f'pre-whitespace inserting: {mini_notation}')

    # insert whitespace between brace and non-brace element
    # user may not supply it.
    # e.g., ']bd' -> '] bd', e.g., 'bd[' -> 'bd ['.
    whitespace_insert_locs = []
    for c_i, c in enumerate(mini_notation[:-1]):
       c_plus_one = mini_notation[c_i + 1]
       if c in right_braces and (c_plus_one not in \
               (list(right_braces) + all_modifier_inits + reserved_symbols)): 
           whitespace_insert_locs.append(c_i + 1)
       elif c_plus_one in normal_left_braces and c \
           not in left_braces:
           whitespace_insert_locs.append(c_i + 1)
    #print(f'whitespace_insert_locs: {whitespace_insert_locs}')            
    for loc_i, loc in enumerate(whitespace_insert_locs):
        mini_notation = utils.insert_str(mini_notation, loc + loc_i, to_insert = " ")

    # removes whitespace at beginning and end of string,
    # and collapses neighboring white spaces to a single space.
    mini_notation = " ".join(mini_notation.split())
    # note:  it may not be the most musical option to always parse things "correctly";
    # e.g., if user has a space between a modifier and its argument,
    # maybe it's more likely that argument is actually missing by accident.
    # in which case it may be better to raise a syntax error.
    # keep this in mind for later.

    # add a leading '[' and closing ']' bracket so everything is 'nested' 
    # (makes parsing easier later).
    mini_notation = '[' + mini_notation + ']'
    return mini_notation



def extract_modifier_brackets(mini_notation):
    """ extracts modifier bracket contents e.g., bd(3, <17 5 [4 3]>, 2) 
    Replaces contents with simply '(', which is parsed as a nullary modifier. 
    Returns the position of the '(' as well as the contents.
    Expects non-informative whitespace to be removed with remove_extra_whitespace().
    if to be optimized:  May be sped up by combining with check_bracket_syntax().
    """
    content_slices = [] # list of slices 
    contents = [] # list of strings
    mb_stack = []
    for i, c in enumerate(mini_notation):
        if c in modifier_brackets.keys():
            mb_stack.append((i,c))
        elif c in modifier_brackets.values():
            left_match = all_bracket_matches[c]
            if ((len(mb_stack) > 0) and (left_match == mb_stack[-1][1])):
                start_pos = mb_stack.pop()[0]
                end_pos = i
                   # len(mb_stack) == 0 ensures we're storing contents of the outermost bracket.  
                   # bd(3(3,8),8) will be retrieved as only one element.
                if len(mb_stack) == 0:   
                    content_slices.append(slice(start_pos, end_pos + 1))
                    contents.append(mini_notation[start_pos:i + 1]) 
    return content_slices, contents 


def get_mb_index_dict(mb_slices, mn):
    """ Takes a list of slices corresponding to the modifier-bracket substring positions and the
    mini-notation string.
    Returns a dictionary for computationally efficient lookup when checking if in modifier bracket.  
    E.g., "bd(3,8) hh(3,8,2)"  would return
    """
    mb_slice_ends = [s.stop - 1 for s in mb_slices]
    mb_index_list = utils.concat([list(range(s.start,s.stop)) for s in mb_slices])

    mb_index_dict = { k : 'mb_end' if k in mb_slice_ends else 'mb' if \
            k in mb_index_list else 'non_mb' for k in range(len(mn))}
    return mb_index_dict

def total_bracket_depth(bracket_stack):
    """ 
    Determines total nested depth of bracket stack structure. Used in parse_brackets() below.
    Excludes modifier braces.
    """
    depth = 0
    for k in normal_left_braces:
        depth += len(bracket_stack[k])
    return depth

# add type hint -> list[tuple]
def parse_brackets(mn : str, check_syntax = False):
    """ input: mini_notation string
    returns a list of the segments with their depth.
    """

    #first optionally check for bracket-based syntax errors.  This this is not the most efficient, but
    #it makes the rest of this code way more managable.
    if check_syntax:
        check_bracket_syntax(mn)
        # tidy the mini_notation by deleting non-informative whitespace.
        mn = remove_extra_whitespace(mn)

    mb_slices, mb_contents = extract_modifier_brackets(mn)

    # For debugging the modifier-bracket slicing process. 
    # TODO: add to logger.
    #print(f'slices: {mb_slices}, contents: {mb_contents}')

    mb_index_dict = get_mb_index_dict(mb_slices, mn)
    

    # dictionary of stacks (counters) for counting bracket depth. 
    all_bracket_stacks = {k : [] for k in left_braces} 

    # control state-- since modifiers like '@' can occur after a bracket
    # The value is None unless a closing bracket is found,
    # in which case the value is the corresponding opening bracket 
    checking_for_modifier = None
    # active modifier bracket, not None when '(' is encountered.
    last_char_index = len(mn) - 1
    for i, c in enumerate(mn):

        # edge case:  final closing ']' brace
        if (i == last_char_index):
            if c == ']': # synthetic closing brace; expected
                # handle 'checking_for_modifier' associated bracket 
                if checking_for_modifier is not None:
                    start = all_bracket_stacks[checking_for_modifier].pop()
                    yield (total_bracket_depth(all_bracket_stacks),\
                        mn[start: i ], start, i - 1)
                # yield the full bracketed string.
                all_bracket_stacks['['].pop()
                yield (total_bracket_depth(all_bracket_stacks),\
                        mn[0: i + 1], 0, i)
                continue
            else:
                error_string = 'Somehow the final character in the pre-processed ' 
                error_string += 'string is not \"]\".  Did you run ' 
                error_string += 'remove_extra_whitespace()? Or run again with check_syntax = True.' 
                raise ValueError(error_string)

        # get information from the brackets including str start and stop positions.
        # handle modifiers that may follow braces.
        if checking_for_modifier is None:
            if c in normal_left_braces and mb_index_dict[i] == 'non_mb':
                all_bracket_stacks[c].append(i)
            elif c in normal_right_braces and mb_index_dict[i] == 'non_mb':
                # when you encounter a closing brace, check for brace modifiers
                # like '@', '!', and '(3,8)'
                # set control value to opening brace.
                checking_for_modifier = all_bracket_matches[c]

        # if last iteration said to check for a modifier
        elif checking_for_modifier is not None:

            # case 1:  in territory of modifier bracket.
            # case 1a:  done with modifier bracket section e.g. ')' is encountered.
            if mb_index_dict[i] == 'mb_end':
                # yield a tuple with depth of bracket contents, its 
                # contents, start char, and end char
                start = all_bracket_stacks[checking_for_modifier].pop()
                yield (total_bracket_depth(all_bracket_stacks),\
                        mn[start: i + 1], start, i - 1)
                checking_for_modifier = None
                continue
            # case 1b: if inside modifier bracket, 
            # ignore the brackets in mininotation inside '()' for now. 
            elif mb_index_dict[i] == 'mb':
                continue

            # case 2:  modifier is finished. two ways this can happen.
            elif c == ' ' or c in all_normal_brackets:
                # bc string was pre-stripped of extraneous whitespace
                # we're done: there's either no modifier or modifier is finished 
                start = all_bracket_stacks[checking_for_modifier].pop()
                yield (total_bracket_depth(all_bracket_stacks),\
                        mn[start: i], start, i - 1)
                if c == ' ': 
                    checking_for_modifier = None
                elif c in normal_right_braces: 
                    # current modifier is done, next iteration check for new eligible modifier.
                    checking_for_modifier = all_bracket_matches[c]

            # case 3:
            # either argument modifier, a modifier's argument, or nullary modifier. 
            # do nothing.

        # for debugging the bracket parsing process. 
        # TODO: add to logger.
        #if c in all_brackets:
        #    print(i,c)
        #    print(all_bracket_stacks)

# Build a string of functions (valid vortex code) that can be executed by running eval().
# there's got to be a better way than using strings.  yield might be a nice way to 
# lazily evaluate functions after being passed around in complex ways.
   
def add_pure(items_list):
    if len(items_list) > 1:
        # don't think i need 'NEXTLEVEL' here
        return [f'pure(\"{x}\")' if x != 'NEXTLEVEL' else x for x in items_list ]
    elif len(items_list) == 1:
        if "NEXTLEVEL" not in items_list[0]:
            return f'pure(\"{items_list[0]}\")'
        else:
            return f'{items_list[0]}'
    else:
        raise ValueError("add_pure applied to an empty list")

def parse_simple_modifiers(item : str) -> str:
    """
    """
    #TODO:  correctly implement subtly different '!' and '*'
    if '!' in item:
        pat,  arg = item.split('!')
        return f'fast ({arg}, pure({pat}))'
    elif '*' in item:
        pat,  arg = item.split('*')
        return f'fast ({arg}, pure({pat}))'
    elif '/' in item:
        pat,  arg = item.split('*')
        return f'slow ({arg}, pure({pat}))'
    elif '@' in item:
        return f'@ coming soon'
    elif '?' in item:
        return f'? coming soon'

def fastcatify(string : str) -> str:
    """
    'a b c d' -> 'fastcat(pure("a"), pure("b"), pure("c"), pure("d")'
    'a' -> 'pure("a")'
    """
    print(f'fastcatify string {string}')
    space_split_items = string.split(' ')
    if len(space_split_items) > 1:
        pure_comma_separated = ",".join(add_pure(space_split_items))
        functions = f'fastcat({pure_comma_separated})'
        return functions
    # delete me when `pure("a")` can be replaced with `a`.
    else:    
        return add_pure([string])

def stackify(function_list) -> str:
    """
    [a, b] -> 'stack(a,b)'
    """
    return f'stack({",".join(function_list)})' 

def parse_euclidean(): 
    """
    One element with one (possibly complex) euclidean modifier
    """
    return None

def parse_non_nested(mn, start, stop, mb_slices):   
    """
    mn is the string mini-notation input.
    mn is non-nested (euclidean may be complex tho), so as complex as [hh?, bd!3](3,8 17 <5>)
    start and stop are coordinates relative to the full mini-notation string)
    mb_slices contains the modifier bracket coordinates (relative to the full mini-notation,
    use them for parsing mini_notation modifiers.
    """
    # TODO:  handle modified brackets e.g. [hh, bd]@5
    # TODO:  handle euclidean commmas e.g. [hh(3,8,1)].  
    # these currently get interpreted as a list to `stack()` 

    print(f'parse_non_nested mn: {mn}')
    content_init = mn[0]
    # strip the beginning and end braces (change if modifier)

    # content is the mini-notation itself, minus brackets
    content = mn[1:-1]
    if content_init == '[': 
        # do mini-notation -> function translation here
        if ',' in content:
            function_list = []
            comma_split_items = content.split(',')
            for csi in comma_split_items:
                function_list.append(fastcatify(csi))
            print(f'comma split func list: {function_list}')
            functions = stackify(function_list)
        else:
            functions = fastcatify(content) 
    elif content_init == '<':
        functions = "< > brackets are currently not handled"
    elif content_init == '{':
        functions = "{ } brackets are currently not handled"
    else:
        functions = f'Strange initiating bracket \"{content_init}\" detected'
    return functions

def build_pattern(current_element, parsed_brackets, mb_slices):
    """
    recurse over nested bracket structure to assemble the pattern out of pattern functions 
    mb_slices handle euclidean rhythms.
    """
    level = current_element[0]
    current_start = current_element[2]
    current_stop = current_element[3]
    # get tree branches.
    next_level = level + 1
    #TODO:  add to logger
    #print(f'parsed_brackets : {parsed_brackets}')
    print(f'current_level : {level}')
    next_level_elements = [x for x in parsed_brackets if x[0] == next_level] \
                           #if x[2] > current_start if x[3] < current_stop]
    print(f'nles: {next_level_elements}')
    """
       next_level:   [--]  <---->              [--]       <---->
                                        ->
    current_level:  -[--]--<---->-----      -NEXTLEVEL-- NEXTLEVEL------
    """
    nle_slices = []
    next_level_results = []
    for nle in next_level_elements: 
        print(f'level : {next_level}')
        print(f'nle: {nle}')
        # recurse, to build the next string of functions
        next_level_results.append(build_pattern(nle, parsed_brackets, mb_slices))
        nle_slices.append(slice(nle[2], nle[3] + 1))
    # now that we've iterated over all next_level elements,
    # all these elements will be replaced with 'NEXTLEVEL'
    print(f'next_level_results: {next_level_results}')
    print(f'nle_slices: {nle_slices}')
    print(f'current_element[1]: {current_element[1]}')
    print(f'current_start: {current_start}')
    substituted_contents = utils.str_slice_replace(current_element[1], \
            nle_slices, 'NEXTLEVEL', offset = current_start)
    #print(f'substituted_contentssubstituted_contents)
    print(f'substituted_contents: {substituted_contents}')
    # because nle's are sorted, we can replace in order.
    function_string = parse_non_nested(substituted_contents,\
            current_element[2], current_element[3], mb_slices)
    print(f'function_string: {function_string}')
    if len(next_level_results) > 0:
        for nlr in next_level_results:
            # replace first instance of 'NEXTLEVEL' with the string of functions.
            function_string = function_string.replace('NEXTLEVEL',nlr,1)
    return function_string
    
  
def parse(mn : str):
    assert isinstance(mn, str)
    # check syntax and remove non-informative whitespace
    check_bracket_syntax(mn)
    mn = remove_extra_whitespace(mn)

    # this is the second time these are computed, but ok for now
    mb_slices, mb_contents = extract_modifier_brackets(mn)
    mb_index_dict = get_mb_index_dict(mb_slices, mn)

    # sort parsed brackets by the start position.
    parsed_brackets = sorted(parse_brackets(mn), key = lambda x : x[2]) 
    # build function string starting with the left-most (and least nested) element.
    function_string = build_pattern(parsed_brackets[0], parsed_brackets, mb_slices)
    print(f'final function_string: {function_string}')    



# functions for testing correct parsing behavior

def print_tidied(mn):
    cleaned_whitespace = remove_extra_whitespace(mn)
    print(f'tidied: {cleaned_whitespace}')
    ruler = [str(x % 10) if ((x%10) != 0) else (str(0) + str(x))[-2] for
             x in range(len(cleaned_whitespace))]
    print(f'ruler:  {"".join(ruler)}')

def print_bracket_parse(mn):
    tidied = remove_extra_whitespace(mn)
    out = list(parse_brackets(tidied))
    print(f'parsed brackets: {out}')

def test_bracket_syntax(mn):
    print(mn)
    try:
        check_bracket_syntax(mn)
        print('untidied passes syntax')
        print_tidied(mn)
    except SyntaxError:
        print('untidied string has syntax error')
    try:
        check_bracket_syntax(remove_extra_whitespace(mn))
        print('tidied passes syntax')
    except SyntaxError:
        print('tidied string has syntax error')
    print('\n')

def full_inspect(mn):
    print(mn)
    print_tidied(mn)
    print_bracket_parse(mn)
    print('\n')

if __name__ == '__main__':

    # run tests
    valid_mns = ['bd <sn cp> bd!3 sn@4 hh ?  ',                                     # simple
                '   bd [<[[ hh] [{hh [bd] } [hh [hh hh]]]] cp>] bd!3 sn@4 hh ?  ', # complex
                ' bd(7,19, 3) [sn hh](3,8, 1) ',                   # valid euclidean rhythms
                ' [hh hh hh] <hh [ hh hh ]> ',                              # test new bug 
                ' bd(<3 5>, 8) ']                                     # pattern in euclidean 

    invalid_mns = ['bd <sn cp>> bd!3 sn@4 hh ?  ',                   # premature closing `>`
                'bd <sn[ cp>] bd!3 sn@4 hh ?  ',                    # `[>]` in bracket stack
                ' bd!3 sn@4 hh ? ( ']                                     # unclosed bracket

    syntax_test_mns= valid_mns + invalid_mns

    check_syntax = False
    check_bracket_parsing = False 
    check_pattern_parsing = True
    if check_syntax:
        for t in syntax_test_mns:
            test_bracket_syntax(t)
    if check_bracket_parsing:
        for t in valid_mns:
            #print_bracket_parse(t)
            full_inspect(t)
    if check_pattern_parsing:
        #for t in ['[a b c d e]', '[a b [c d [d e ]] g h [i j]]', '[a,b]','[a,[b c]]']:  #valid_mns:
        #for t in  ['a [b c] [d e [ f g]] ']:  #valid_mns:
        for t in  ['[a [ b c]] [e ] ']:  #valid_mns:
        #for t in ['[a [b c ] d [e f]]']:  #valid_mns:
            print_tidied(t)
            start = time.time()
            parse(t)
            elapsed = time.time() - start
            print(f'time elapsed: {elapsed}')
            print('\n')


