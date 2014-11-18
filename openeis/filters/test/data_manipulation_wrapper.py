import csv
import json
import math
import os
import shutil
import traceback
import tempfile

from openeis.filters.apply_filter import apply_filter_config
from openeis.projects.models import (SensorIngest,)
from openeis.projects import models


def run_data_manipulation(config, expected):
    exe = DataManipulationwrapper()
    exe.run_data_manipulation(config, expected)
    


class DataManipulationwrapper:
    
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
            
    def assertIn(self, value, collection, msg=None):
        if msg:
            assert value in collection, msg
        else:
            assert value in collection
            
    def run_data_manipulation(self, config, expected):
        
        dataset_id = int(config['global_settings']['dataset_id'])
        config_string = config['global_settings']['config']
        config = json.loads(config_string)
        
        result = apply_filter_config(dataset_id,config)
        if isinstance(result,list):
            print('Error = ',result) 
        else:
            print('New dataset id =',result)
        
        dataset = SensorIngest.objects.get(pk= result)
        assert dataset != None
        assert dataset.id == dataset_id + 1
        rows = dataset.merge()
    
        tmp_dir = tempfile.mkdtemp()
        print(tmp_dir)
        temp_file = os.path.join(tmp_dir,"output.csv")
        with open(temp_file, 'w', newline='\n') as fout:
            csvwriter = csv.writer(fout)
            for r in rows:
                csvwriter.writerow(r)
        
        actual_rows = self._getCSV_asList(temp_file)
        expected_rows = self._getCSV_asList(expected)
        self._diff_checker(expected_rows, actual_rows)
            
        shutil.rmtree(tmp_dir, ignore_errors=True)
        
        
        

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

