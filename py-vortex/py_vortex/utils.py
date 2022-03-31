from functools import partial
from fractions import Fraction
import operator

def concat(lst) -> list:
    """Flattens a list of lists"""
    return [item for sublist in lst for item in sublist]

def remove_nones(lst) -> list:
    """Removes 'None' values from given list"""
    return filter(lambda x: x != None, lst)

def id(x):
    """Identity function"""
    return x

def merge_dicts(a, b, op=operator.add):
    return dict(a.items() + b.items() +
        [(k, op(a[k], b[k])) for k in set(b) & set(a)])

def partial_function(f):
    """Decorator for functions to support partial application. When not given enough 
    arguments, a decoracted function will return a new function for the remaining 
    arguments"""
    def wrapper(*args):
        try:
            return f(*args)
        except (TypeError) as e:
            return partial(f, *args)
    return wrapper

def show_fraction(frac):
    if frac == None:
        return "None"

    if frac.denominator == 1:
        return str(frac.numerator)

    lookup = {Fraction(1, 2): "½",
              Fraction(1, 3): "⅓",
              Fraction(2, 3): "⅔",
              Fraction(1, 4): "¼",
              Fraction(3, 4): "¾",
              Fraction(1, 5): "⅕",
              Fraction(2, 5): "⅖",
              Fraction(3, 5): "⅗",
              Fraction(4, 5): "⅘",
              Fraction(1, 6): "⅙",
              Fraction(5, 6): "⅚",
              Fraction(1, 7): "⅐",
              Fraction(1, 8): "⅛",
              Fraction(3, 8): "⅜",
              Fraction(5, 8): "⅝",
              Fraction(7, 8): "⅞",
              Fraction(1, 9): "⅑",
              Fraction(1,10): "⅒"
    }
    if frac in lookup:
        result = lookup[frac]
    else:
        result = "(%d/%d)" % (frac.numerator, frac.denominator)
    return result

def insert_str(string : str, loc : int, to_insert = " "):
    """
    Inserts substring (usually whitespace) into the string at position loc
    """
    if not isinstance(loc, int):
        raise ValueError('loc is not an int.  did you mean to use str_slice_replace?')
    return string[:loc] + to_insert + string[loc:]

def str_slice_replace(string, slices, replacements, offset = 0):
    """
    replace a slice of a string with replacement string.
    or replace a list of slices with a list of replacement strings 
    list must be sorted from left to right.
    offset is used if the string's first character does 
    not correspond to index 0.
    """
    if isinstance(slices, list):
        if len(slices) > 0:
            for i in reversed(range(len(slices))):
                print(f'string; {string}')
                head = string[:(slices[i].start - offset)] 
                print(f'string head: {head}')
                tail = string[(slices[i].stop - offset):]
                print(f'string tail: {tail}')
                if isinstance(replacements, list):
                    string = head + replacements[i] + tail
                    print(f'string head + mid +  tail: {string}')
                elif isinstance(replacements, str):
                    string = head + replacements + tail
                else:
                    raise ValueError('\"replacements\" is not a list or string')
        elif len(slices) == 0:
            return string
    elif isinstance(slices, slice):
        if not isinstance(replacements, str):
            raise ValueError('a single slice supplied but replacements is not a string.')
        else:
            string = string[:(slices.start - offset)] + replacements + string[(slices.stop - offset):]
    return string

