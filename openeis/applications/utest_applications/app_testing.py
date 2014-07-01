"""
Module for testing applications.
"""

from subprocess import call
from configparser import ConfigParser
import csv
import os
import math
import sys

def set_up_fixtures(fixtures):
    """
    Install the given fixtures.  Can tolerate more than one fixture.
    """
    # Flush current database
    call(['openeis', 'flush', '--verbosity=0', '--noinput'])

    install = ['openeis', 'loaddata']
    install.extend(fixtures)
    # install fixtures
    call(install)

def tear_down_fixtures():
    """
    Flush the database.
    """
    call(['openeis', 'flush', '--verbosity=0', '--noinput'])

def call_runapplication(apps, config_file):
    """
    Runs the application, checks if a file was outputted from the application.
    It can tolerate more than one output file for an application run.
    Parameters: application names as a list, configuration file
    Returns: The file made from the application.
    Throws: Assertion error if no new file was created.
    """
    # Get all files
    all_files_before = os.listdir()
    # Dictionary to hold app files before running application.
    app_dict_before = {}
    # Filter for csv files with app name in it.
    for application in apps:
        app_dict_before[application] = [k for k in all_files_before \
                                        if (application in k and '.csv' in k)]
    #all_app_outputs_before = \
    #        [k for k in all_files_before if (app in k and '.csv' in k)]
    # Call runapplication on the configuration file.
    call(['openeis', 'runapplication', config_file])
    # List all files
    all_files_after = os.listdir()
    # Dictionary to hold app files after running application
    app_dict_after = {}
    # Filter
    for application in apps:
        app_dict_after[application] = [k for k in all_files_after \
                                       if (application in k and '.csv' in k)]
    # Make sure a new file was made
    newest = []
    for app in apps:
        assert len(app_dict_after[app]) > len(app_dict_before[app]),\
                "Error:  No new file was created for " + app + "."
        # Grab the newest one that is made from the application.
        newest.append(max(app_dict_after[app], key=os.path.getctime))
    return newest

def list_outputs(test_output, expected_output):
    """
    Returns outputs from test outputs and expected outputs.  To be compared in
    the test.
    """
    # Open the files
    test_file = open(test_output, 'r')
    expected_file = open(expected_output, 'r')

    # Create respective reader and writers
    test_reader = csv.reader(test_file)
    expected_reader = csv.reader(expected_file)

    # Listify
    test_list = list(test_reader)
    expected_list = list(expected_reader)

    # Close the files
    test_file.close()
    expected_file.close()

    return test_list, expected_list

def diff_checker(test_list, expected_list):
    """
    Checks for differences between the new csv file and the expected csv file. 
    If the values are strings, it's checked for exactness.  Numerical values are
    checked using the nearly_same function below.
    """
    test_dict = {}
    expected_dict = {}

    for test_header in test_list[0]:
        test_dict[test_header] = []

    for expected_header in expected_list[0]:
        expected_dict[expected_header] = []

    i = 0
    for elem in test_list:
        for m in test_list[0]:
            test_dict[m].append(elem[i%len(test_list[0])])
            i += 1

    i = 0
    for elem in expected_list:
        for m in expected_list[0]:
            expected_dict[m].append(elem[i%len(expected_list[0])])
            i += 1

    # Check for differences.
    i = 1
    for key in test_dict:
        if (is_num(test_dict[key][1])):
            assert (test_dict[key][0] == expected_dict[key][0]), \
                "Headers don't match."
            # Arrays to hold numerical values of this column. 
            # (They're parsed as strings to begin with.)
            test_val_arr = []
            expe_val_arr = []
            for val in test_dict[key][1:]:
                test_val_arr.append(float(val))
                expe_val_arr.append(float(expected_dict[key][i]))
                i += 1
            # Check for approximate sameness.
            assert (nearly_same(test_val_arr, expe_val_arr)),\
                    "Values don't match for '" + key + "' header."
        else:
            assert (test_dict[key] == expected_dict[key]), \
                "Something in the " + key + " header doesn't match."
        i = 1


#Taken directly from reference code.
def nearly_same(xxs, yys, absTol=1e-12, relTol=1e-6):
    """
    Compare two numbers or arrays, checking all elements are nearly equal.
    """
    # Coerce scalar to array if necessary.
    if( not hasattr(xxs, '__iter__') ):
        xxs = [xxs]
    if( not hasattr(yys, '__iter__') ):
        yys = [yys]

    # Initialize.
    lenXX = len(xxs)
    nearlySame = (len(yys) == lenXX)

    idx = 0
    while( nearlySame and idx<lenXX ):
        xx = xxs[idx]
        absDiff = math.fabs(yys[idx]-xx)
        if( absDiff>absTol and absDiff>relTol*math.fabs(xx) ):
            print ('Not nearly same:', xx, yys[idx], 'idx:',idx, 'absDiff:',\
                   absDiff, 'relDiff:',absDiff/math.fabs(xx))
            nearlySame = False
        # Prepare for next iteration.
        idx += 1

    return(nearlySame)

def is_num(s):
    """
    Check to see if it's a number.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False

# maybe one day do log files.
def run_test(ini_file, expected_outputs, clean_up=False):
    """
    Testing script that expects stuff and things.
    Parameters: -First argument should be the ini file
                -Second argument should be the expected output
    """
    config = ConfigParser()
    # read the init file
    config.read(ini_file)
    # grab application name
    application = [config['global_settings']['application']]
    if (application[0] == 'energy_signature'):
        application[0] = "Scatterplot"
        application.append("Weather Sensitivity")
    # get fixtures to be installed
    fixtures = config['global_settings']['fixtures'].split(',')
    # set up fixtures
    set_up_fixtures(fixtures)
    # run application
    test_output = call_runapplication(application, ini_file)
    i = 0
    for output in test_output:
        # get outputs
        test_list, expected_list = list_outputs(output, expected_outputs[i])
        # check for similarity
        diff_checker(test_list, expected_list)
        i += 1

    if clean_up:
        if (application[0] == "Scatterplot"):
            application[0] = "energy_signature"
        for output in test_output:
            os.remove(output)
        allFiles = [k for k in os.listdir() if (application[0] in k and '.log' in k)]
        newestLog = max(allFiles, key=os.path.getctime)
        os.remove(newestLog)


    tear_down_fixtures()

"""
Can be called from the command line.
First argument should be the configuration file, followed by expected outputs.
Use '-clean' at the end for no outputs.
"""
if __name__ == '__main__':
    try:
        if ((sys.argv[1] == '-h') or (sys.argv[1] == '-help')):
            print("First argument should be the configuration file,\n\
                followed by expected outputs.\n\
                Use '-clean' at the end for no outputs.")
            sys.exit()
        clean = False
        ini_file = sys.argv[1]
        expected_output = []
        for arg in sys.argv[2:]:
            if (arg == "-clean"):
                clean = True
                break
            expected_output.append(arg)
        run_test(ini_file, expected_output, clean)
        print("==========\nWOW THAT TEST PASSED! WOO! \n==========\n")
    except KeyError:
        print("\nError: Something is wrong with your configuration file.\n")
    except FileNotFoundError:
        print("\nAn expected output file does not exist.\n")


