"""
Module for testing applications.
"""

from django.test import TestCase
from subprocess import call
from configparser import ConfigParser
import csv
import os
import math
import sys

from openeis.applications import get_algorithm_class
from openeis.projects.storage.db_output import DatabaseOutputFile
from openeis.projects.storage.db_input import DatabaseInput

class AppTestBase(TestCase):
    # Taken directly from runapplication command.
    def run_application(self, config_file):
        config = ConfigParser()

        config.read(config_file)

        application = config['global_settings']['application']
        klass = get_algorithm_class(application)

        dataset_ids = None
        if config.has_option('global_settings', 'dataset_id'):
            dataset_id_string = config['global_settings']['dataset_id']
            dataset_ids = [int(x) for x in dataset_id_string.split(',')]

        sensormap_id = int(config['global_settings']['sensormap_id'])
        topic_map = {}

        inputs = config['inputs']
        for group, topics in inputs.items():
            topic_map[group] = topics.split()


        db_input = DatabaseInput(sensormap_id, topic_map,
                dataset_ids=dataset_ids)

        output_format = klass.output_format(db_input)
        file_output = DatabaseOutputFile(application, output_format)

        kwargs = {}
        if config.has_section('application_config'):
            for arg, str_val in config['application_config'].items():
                kwargs[arg] = eval(str_val)

        app = klass(db_input, file_output, **kwargs)
        app.execute()

    def call_runapplication(self, tables, config_file):
        """
        Runs the application, checks if a file was outputted from the
        application.  It can tolerate more than one output file for an
        application run.

        Parameters: application names as a list, configuration file
        Returns: The file made from the application.
        Throws: Assertion error if no new file was created.
        """
        # Get all files
        all_files_before = os.listdir()
        # Dictionary to hold app files before running application.
        app_dict_before = {}
        # Filter for csv files with app name in it.
        for table in tables:
            app_dict_before[table] = [k for k in all_files_before \
                                            if (table in k and '.csv' in k)]
        # Call runapplication on the configuration file.
        self.run_application(config_file)
        # List all files
        all_files_after = os.listdir()
        # Dictionary to hold app files after running application
        app_dict_after = {}
        # Filter
        for table in tables:
            app_dict_after[table] = [k for k in all_files_after \
                                           if (table in k and '.csv' in k)]
        # Make sure a new file was made
        newest = {}
        for table in tables:
            self.assertTrue(\
                (len(app_dict_after[table]) > len(app_dict_before[table])),\
                "Error:  No new file was created for " + table + ".")
            # Grab the newest one that is made from the application.
            newest[table] = max(app_dict_after[table], key=os.path.getctime)
        return newest

    def list_outputs(self, test_output, expected_output):
        """
        Returns outputs from test outputs and expected outputs.  To be compared
        in the test.
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

    def diff_checker(self, test_list, expected_list):
        """
        Checks for differences between the new csv file and the expected csv
        file. If the values are strings, it's checked for exactness.  Numerical
        values are checked using the nearly_same function below.
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
            if (self.is_num(test_dict[key][1])):
                self.assertEqual(test_dict[key][0], expected_dict[key][0],\
                        "Headers don't match.")
                # Arrays to hold numerical values of this column.
                # (They're parsed as strings to begin with.)
                test_val_arr = []
                expe_val_arr = []
                for val in test_dict[key][1:]:
                    test_val_arr.append(float(val))
                    expe_val_arr.append(float(expected_dict[key][i]))
                    i += 1
                # Check for approximate sameness.
                self.nearly_same(test_val_arr, expe_val_arr, key)
            else:
                self.assertEqual(test_dict[key], expected_dict[key], \
                    "Something in the " + key + " header doesn't match. They \
                    are " + str(test_dict[key]) + ',' + \
                    str(expected_dict[key])+ '.')
            i = 1


    def is_num(self, s):
        """
        Check to see if it's a number.
        """
        try:
            float(s)
            return True
        except ValueError:
            return False

    def nearly_same(self, xxs, yys, key):
        """
        Compare two numbers or arrays, checking all elements are nearly equal.
        """
        # Coerce scalar to array if necessary.
        if( not hasattr(xxs, '__iter__') ):
            xxs = [xxs]
        if( not hasattr(yys, '__iter__') ):
            yys = [yys]

        assert len(xxs) == len(yys),\
                "The two compared arrays must be of equal length."

        idx = 0
        while(idx < len(xxs)):
            self.assertAlmostEqual(xxs[idx], yys[idx], msg=(str(xxs[idx]) +\
                    " is not equal to " + str(yys[idx]) + ". This is under " +\
                    key))
            idx += 1

    def run_it(self, ini_file, expected_outputs, clean_up=False):
        """
        Testing script.
        Parameters: -First argument should be the ini file
                    -Second argument should be the expected output
        """
        config = ConfigParser()
        # read the init file
        config.read(ini_file)
        # grab application name
        application = config['global_settings']['application']
        # run application
        test_output = self.call_runapplication(expected_outputs.keys(), \
                                               ini_file)
        for table in expected_outputs:
            # get outputs
            test_list, expected_list = \
                self.list_outputs(test_output[table], expected_outputs[table])
            # check for similarity
            self.diff_checker(test_list, expected_list)

        if clean_up:
            for output in test_output:
                os.remove(test_output[output])
            allFiles = [k for k in os.listdir() if \
                    (application in k and '.log' in k)]
            newestLog = max(allFiles, key=os.path.getctime)
            os.remove(newestLog)


