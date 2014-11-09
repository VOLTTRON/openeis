"""
Module for testing applications.


Copyright
=========

OpenEIS Algorithms Phase 2 Copyright (c) 2014,
The Regents of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the U.S.
Department of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov
referring to "OpenEIS Algorithms Phase 2 (LBNL Ref 2014-168)".

NOTICE:  This software was produced by The Regents of the University of
California under Contract No. DE-AC02-05CH11231 with the Department of Energy.
For 5 years from November 1, 2012, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, and perform
publicly and display publicly, by or on behalf of the Government. There is
provision for the possible extension of the term of this license. Subsequent to
that period or any extension granted, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, distribute copies
to the public, perform publicly and display publicly, and to permit others to
do so. The specific term of the license can be identified by inquiry made to
Lawrence Berkeley National Laboratory or DOE. Neither the United States nor the
United States Department of Energy, nor any of their employees, makes any
warranty, express or implied, or assumes any legal liability or responsibility
for the accuracy, completeness, or usefulness of any data, apparatus, product,
or process disclosed, or represents that its use would not infringe privately
owned rights.


License
=======

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
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


class AppWrapper:
#     '''
#     A wrapper around the application class to allow for input/output
#     comparisions made easy.
#     '''
#     def __init__(self, config_file, result_dict):
#         '''
#         Pass the configuration file that should be used to run the application.
#         The result dictionary should contain the output that is
#         expected from the application in the form of 
#         {
#             'SENSOR_Table': 'C:/temp/data.csv'
#         }
#         '''
#         self.config = config_file
#         self.results = result_dict
#         
#         assert os.path.exists(config_file)
#         for v in result_dict.values():
#             assert os.path.exists(v)

    def assertTrue (self, given, msg=None):
        if msg:
            assert given == True, msg
        else:
            assert given == True
            
    def assertEqual(self, given, expected, msg=None):
        if msg:
            assert given == expected, msg
        else:
            assert given == expected

    def run_application(self, configFileName):
        """
        Runs the application with a given configuration file.
        Parameters:
            - configFileName: configuration file for application run
        Returns:
            - actual_outputs, dictionary, maps table name to file name of run results
        """

        # Note the overall process here follows that of method
        # openeis/projects/management/commands/runapplication.handle().

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
        analysis = models.Analysis(
            added=now, started=now, status="running",
            dataset=dataset, application=appName,
            debug=True,
            project_id = dataset.project_id,
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

        # Execute the application.
        app = klass(db_input, file_output, **kwargs)
        try:
            app.run_application()
            for report in klass.reports(output_format):
                print(report)
            
        except Exception as ee:
            #analysis.status = 'error'
            # Re-raise the exception, since testing may include checking for expected exceptions.
            raise( ee )
        finally:
            
            analysis.ended = datetime.datetime.utcnow().replace(tzinfo=utc)
            analysis.save()

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
            # Get application name from config file.
            self.assertTrue(
                os.path.isfile(configFileName),
                msg='Cannot find configuration file "{}"'.format(configFileName)
                )
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
