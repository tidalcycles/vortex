from functools import partial

def concat(lst) -> list:
    """Flattens a list of lists"""
    return [item for sublist in lst for item in sublist]

def remove_nones(lst) -> list:
    """Removes 'None' values from given list"""
    return filter(lambda x: x != None, lst)

def id(x):
    """Identity function"""
    return x

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
