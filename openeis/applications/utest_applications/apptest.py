"""
Module for testing applications.
"""

import datetime
import csv
import os
import math

from django.test import TestCase
from django.utils.timezone import utc
from configparser import ConfigParser

from openeis.applications import get_algorithm_class
from openeis.projects.storage.db_output import DatabaseOutputFile
from openeis.projects.storage.db_input import DatabaseInput
from openeis.projects import models


class AppTestBase(TestCase):


    def run_application(self, configFileName):
        """
        Runs the application with a given configuration file.
        Parameters:
            - configFileName: configuration file for application run
        Returns:
            - actual_outputs, dictionary, maps table name to file name of run results
        """

        # Read the configuration file.
        config = ConfigParser()
        config.read(configFileName)

        # Get application.
        appName = config['global_settings']['application']
        klass = get_algorithm_class(appName)

        # Check which data set we're using
        dataset_id = int(config['global_settings']['dataset_id'])
        dataset = models.SensorIngest.objects.get(pk=dataset_id)

        # Get application parameters.
        kwargs = {}
        if config.has_section('application_config'):
            for arg, str_val in config['application_config'].items():
                kwargs[arg] = eval(str_val)

        # Get application inputs.
        inputs = config['inputs']
        topic_map = {}
        for group, topics in inputs.items():
            topic_map[group] = topics.split()

        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        project = models.Project.objects.get(pk=1)
        analysis = models.Analysis(project=project,
            added=now, started=now, status="running",
            dataset=dataset, application=appName,
            configuration={
                'parameters': kwargs,
                'inputs': topic_map
                },
            name='cli: {}, dataset {}'.format(appName, dataset_id)
            )
        analysis.save()

        db_input = DatabaseInput(dataset.map.id, topic_map, dataset_id)

        output_format = klass.output_format(db_input)
        file_output = DatabaseOutputFile(analysis, output_format)

        app = klass(db_input, file_output, **kwargs)

        # Execute the application
        app.run_application()

        # Retrieve the map of tables to output CSVs from the application
        actual_outputs = {}
        for tableName in app.out.file_table_map.keys():
            actual_outputs[tableName] = app.out.file_table_map[tableName].name

        return actual_outputs


    def _getCSV_asList(self, csvFileName):
        """
        Return contents of a CSV file as a list.

        Parameters:
            - csvFileName: name of CSV file
        Output:
            - contents: list of file contents.
              Each list element is itself a list, giving one row of the file.
              Each row-list has one element per column.
        """
        self.assertTrue(
            os.path.isfile(csvFileName),
            msg='Cannot find CSV file {' +csvFileName +'}'
            )
        with open(csvFileName, 'r') as ff:
            reader = csv.reader(ff)
            contents = list(reader)
        return( contents )


    def _diff_checker(self, test_list, expected_list):
        """
        Check for differences between the new csv file and the expected csv
        file. If the values are strings, it's checked for exactness.  Numerical
        values are checked using the nearly_same function defined below.

        Parameters:
            - test_list: test file contents in a list
            - expected_list: expected file contents as a list
        Throws:
            - Assertion error if the numbers are not nearly same, or the file
                does not match
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
            self.assertTrue((len(test_dict[key]) > 1),
                    "The application did not run correctly.")
            if (self._is_num(test_dict[key][1])):
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

    def _is_num(self, s):
        """
        Check to see if s a number.

        Parameters:
            - s: a number.
        Returns:
            - True or False indicating if given s is a number.
        """
        try:
            float(s)
            return True
        except ValueError:
            return False


    def nearly_same(self, xxs, yys, key='', absTol=1e-12, relTol=1e-6):
        """
        Compare two numbers or arrays, checking all elements are nearly equal.

        Parameters:
            - xxs, yys: two lists of numbers to compare
            - key: the key to the column we are comparing in output files
            - absTol: absolute tolerance
            - relTol: relative tolerance
        Returns: True if the two lists are nearly the same; else False.  TODO: Actually, assertion error in that case, but this may change.
        Throws: Assertion error if xxs and yys not nearly the same.
        """
        #
        # Coerce scalar to array if necessary.
        if( not hasattr(xxs, '__iter__') ):
            xxs = [xxs]
        if( not hasattr(yys, '__iter__') ):
            yys = [yys]
        lenXX = len(xxs)
        nearlySame = (len(yys) == lenXX)
        idx = 0
        while( nearlySame and idx<lenXX ):
            xx = xxs[idx]
            absDiff = math.fabs(yys[idx]-xx)
            if (absDiff>absTol and absDiff>relTol*math.fabs(xx)):
                self.assertFalse((absDiff>absTol and \
                        absDiff>relTol*math.fabs(xx)),
                    (key + ' is not nearly same: ' + str(xx) + ' ' \
                    + str(yys[idx]) + ' idx: ' + str(idx) + ' absDiff: ' \
                    + str(absDiff), ' relDiff: '+ str(absDiff/math.fabs(xx))))
                nearlySame = False
            idx += 1
        return( nearlySame )


    def run_it(self, configFileName, expected_outputs, clean_up=False):
        """
        Runs the application and checks the output with the expected output.
            Will clean up output files if clean_up is set to true.

        Parameters:
            - configFileName: configuration file for application run
            - expected_outputs: dictionary, maps table name to file name of expected results
            - clean_up: if it should clean newly made files or not
        Throws: Assertion error if the files do not match.
        """

        # Read the configuration file.
        config = ConfigParser()
        config.read(configFileName)

        # Get application name.
        appName = config['global_settings']['application']
        # TODO: This, and config above, is not needed unless {clean_up}.

        # Run application.
        actual_outputs = self.run_application(configFileName)

        # Check results.
        for tableName in expected_outputs:
            test_list = self._getCSV_asList(actual_outputs[tableName])
            expected_list = self._getCSV_asList(expected_outputs[tableName])
            self._diff_checker(test_list, expected_list)

        if clean_up:
            for tableName in actual_outputs:
                os.remove(actual_outputs[tableName])
            logFiles = [
                fileName for fileName in os.listdir()  \
                    if (appName in fileName and '.log' in fileName)
                ]
            # TODO: Since log file should now be in a temporary directory,
            # consider just deleting all matching log files.
            if( len(logFiles) > 0 ):
                newestLog = max(logFiles, key=os.path.getctime)
                os.remove(newestLog)
