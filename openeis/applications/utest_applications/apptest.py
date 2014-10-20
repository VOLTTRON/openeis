"""
Module for testing applications.
"""

import datetime
import csv
import os
import math
import sys

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
        self.assertTrue(
            os.path.isfile(configFileName),
            msg='Cannot find configuration file "{}"'.format(configFileName)
            )
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
            msg='Cannot find CSV file "{}"'.format(csvFileName)
            )
        with open(csvFileName, 'r') as ff:
            reader = csv.reader(ff)
            contents = list(reader)
        return( contents )


    def _diff_checker(self, expected_rows, actual_rows):
        """
        Check for differences between two lists.

        Expect lists-of-lists:
            - Interpret each element of the outer list as a row.
            - Interpret each element of the inner list as a column.

        Interpreting rows:
            - The count of rows should match.
            - The order of rows should match.
            - The first row contains column headers.

        Interpreting columns:
            - The count of columns should match.
            - The order of columns does not have to match between the two
              lists.  That is, the column headers may appear in a different
              order between the two lists.  However, the columns should have
              the same headers, and the contents under each header should
              match.

        When comparing the column contents:
            - Expect all entries to be strings.
            - If the string can be coerced to a number, check values for "closeness".
            - Check strings for exactness.

        Parameters:
            - expected_rows: expected file contents
            - actual_rows: actual file contents

        Throws:
            - Assertion error if the contents do not match
        """

        # Check have enough data to work with.
        rowCt_xpd = len(expected_rows)
        self.assertTrue(
            rowCt_xpd > 1,
            msg='The expected results file must have a row of headers and at least one row of data'
            )
        self.assertEqual(
            len(actual_rows), rowCt_xpd,
            msg='The actual results file has {} rows; expecting {}'.format(
                len(actual_rows), rowCt_xpd
                )
            )

        # Assemble dictionaries that map a column-header name to its
        # integer index in the row-list.
        colNameToIdx_xpd = {}
        colCt_xpd = 0
        for colName in expected_rows[0]:
            colNameToIdx_xpd[colName] = colCt_xpd
            colCt_xpd += 1
        self.assertTrue(
            colCt_xpd > 0,
            msg='The expected results file has no entries'
            )

        colNameToIdx_act = {}
        colCt_act = 0
        for colName in actual_rows[0]:
            colNameToIdx_act[colName] = colCt_act
            colCt_act += 1

        # Check all columns of the expected results file.
        for colName in colNameToIdx_xpd:

            # Get column indices.
            colIdx_xpd = colNameToIdx_xpd[colName]
            self.assertIn(
                colName, colNameToIdx_act,
                msg='The actual results file is missing column label "{}"'.format(colName)
                )
            colIdx_act = colNameToIdx_act[colName]

            # Check all rows of this column.
            for rowIdx in range(1,rowCt_xpd):  # Note assuming this is Python3, otherwise, use xrange.

                # Get entries.
                #   Note these are strings.
                str_xpd = expected_rows[rowIdx][colIdx_xpd]
                str_act = actual_rows[rowIdx][colIdx_act]

                # Coerce to numbers if possible.
                num_xpd = self._is_num(str_xpd)
                num_act = self._is_num(str_act)

                # Compare.
                if( (num_xpd is not None) and (num_act is not None) ):
                    # Here, compare as numbers:
                    self.assertTrue(
                        self.nearly_same(num_xpd, num_act),
                        msg='For column "{}", row {} of actual results file has <{}>; expecting <{}>; relative error <{}>'.format(
                            colName, rowIdx+1, str_act, str_xpd,
                            (math.fabs(num_xpd-num_act)/math.fabs(num_xpd) if( num_xpd != 0 ) else 'inf')
                            )
                        )
                elif( str_xpd != str_act ):
                    # Here, compared as strings.
                    #   Note did not use "self.assertEqual()" on the two strings,
                    # which would be the idiomatic way to test.  This is because the
                    # output from assertEqual() gets quite ugly for long strings.
                    self.assertTrue(
                        False,
                        msg='For column "{}", row {} of actual results file has:\n-- "{}";\nexpecting:\n-- "{}"'.format(
                            colName, rowIdx+1, str_act, str_xpd
                            )
                        )

                # Here, done checking entries for this row of this column.

            # Remove this column from the actual results.
            #   To facilitate further checking later.
            del colNameToIdx_act[colName]

        # Here, done checking all columns of the expected results file.
        if( len(colNameToIdx_act) != 0 ):
            self.assertTrue(
                False,
                msg='The actual results file has unexpected column "{}"'.format(
                    list(colNameToIdx_act.keys())[0]
                    )
                )


    def _is_num(self, ss):
        """
        Check to see if a string ss is a number.

        Parameters:
            - ss: a number.
        Returns:
            - A number, or None.
        """
        try:
            ss = float(ss)
        except ValueError:
            ss = None
        return ss


    def nearly_same(self, xx, yy, absTol=1e-12, relTol=1e-6):
        """
        Compare two numbers.

        Parameters:
            - xx, yy: two numbers to compare
            - absTol: absolute tolerance
            - relTol: relative tolerance
        Returns: True if the two numbers are nearly the same; else False.
        """
        nearlySame = True
        absDiff = math.fabs(yy - xx)
        if( absDiff>absTol and absDiff>relTol*math.fabs(xx) ):
            nearlySame = False
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
        self.assertTrue(
            os.path.isfile(configFileName),
            msg='Cannot find configuration file "{}"'.format(configFileName)
            )

        # Run application.
        actual_outputs = self.run_application(configFileName)

        # Check results.
        for tableName in expected_outputs:
            # Provide file names to facilitate debugging.
            #   Note by default {py.test} only shows output to {stdout} and {stderr}
            # if a test fails.  To force the line below to show, run with flag "-s".
            sys.stderr.write('Comparing expected output in "{}" to actual output in "{}"'.format(
                expected_outputs[tableName], actual_outputs[tableName]
                ))
            expected_rows = self._getCSV_asList(expected_outputs[tableName])
            actual_rows = self._getCSV_asList(actual_outputs[tableName])
            self._diff_checker(expected_rows, actual_rows)

        if clean_up:
            for tableName in actual_outputs:
                os.remove(actual_outputs[tableName])
            # Get application name.
            config = ConfigParser()
            config.read(configFileName)
            appName = config['global_settings']['application']
            # Remove log file.
            logFiles = [
                fileName for fileName in os.listdir()  \
                    if (appName in fileName and '.log' in fileName)
                ]
            # TODO: Since log file should now be in a temporary directory,
            # consider just deleting all matching log files.
            if( len(logFiles) > 0 ):
                newestLog = max(logFiles, key=os.path.getctime)
                os.remove(newestLog)
