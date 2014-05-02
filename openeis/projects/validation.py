'''
Created on Apr 29, 2014

A collection of validation functions to reuse throughout the projects
'''

def is_valid_name(name):
    """
    Validate whether a name has been entered with at least
    one character and is not None
    """
    return name != None and len(name.strip()) > 0
