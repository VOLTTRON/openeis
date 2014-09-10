# OpenEIS Unit Testing Applications Guide


## Introduction

This section describes creating and running unit tests for applications hosted under OpenEIS.
This involves:

+ Setting up the data the application needs to run, including raw data and configuration parameters.
+ Running the application, either individually or as part of a suite of automated tests.
+ Checking the output against expected results.

Accordingly, each test of an application comprises an input data file, a fixture file (which stores the input data as a database), a configuration file, and the expected output.

Testing an application typically requires multiple individual tests, covering a range of inputs.
For example, a statistical application may have tests covering "normal" data, data with missing values, data with no variance, and so on.
The expected output from each test can then include checking that the application fails in a controlled way, given bad data.

In this document, the term _unit test_ generally refers to a single run of the application.
The term _application-level test_ refers to the collection of unit tests for the application.


## Overview

The following steps create a unit test:

+ Set up the inputs.
    + Create an input data file.
    + Import the input file to a database.
    + Save the database as a fixture.
+ Create the corresponding expected output file.
+ Place the files in an application-level test directory.

An input file is uploaded to the database and thus may have many different sensor maps derived from it.
As a result, you may use an input file to test many different types of input.
Each column is allowed to have different data that you may test on.
Also, it is possible for sensormaps and datasets to derive from multiple input files.
So if you only had "temperature" in one file and "loads" in another, you may make single sensor map out of the two files.
The input files, sensor maps, datasets are all stored on the database.


These files can be put into what Django calls "fixtures", which are JSON files that hold the everything that has been put into the database.
Django uses fixtures to install whatever you had on the database to test on.
Therefore, you can also have multple tests for a fixture.
You may also install more than one fixture to run a single test, however you should be cautious.
For more on that, please refer to the _Restoring a database from a fixture_ section.


After creating a unit test:

+ The test may be run individually, e.g., as part of the application development.
+ The test may be run as part of an application-level automated test suite.

The unit tests use [Django's testing framework](https://docs.djangoproject.com/en/1.6/topics/testing/).
When run as part of a larger suite of tests, Django creates an isolated environment for each unit test.
As a result, unit tests should not depend on each other.
Furthermore, the individual unit tests execute in no particular order.


## Application-level test directory

The application-level test directory stores the unit test files for a particular application.
Make this a subdirectory of

    openeis_root/openeis/applications/utest_applications

where `openeis_root` is the root directory that contains the OpenEIS project files.
Note that the examples given here use a Unix-style forward slash (`/`) as the file path separator.
On Windows machines, substitute a DOS-style backward slash (`\`).

This subdirectory will contain all the required files for testing the application.
These include data files, configuration files, and expected output files.

For an application called `app_name`, the suggested test subdirectory is

    openeis_root/openeis/applications/utest_applications/app_name


## Input data

Create a file that contains sample data for the application.
A single input file can include data for multiple unit tests.
For example:

datetime    | status | missing | const | floats
:-----------|-------:|--------:|------:|:------
6/1/14 0:00 | 1      | 0       | 7     | 0.0
6/1/14 1:00 | 2      | 1       | 7     | 1
6/1/14 2:00 | 3      |         | 7     | 2.
6/1/14 3:00 | 1      | 3       | 7     | 3.0
6/1/14 4:00 | 2      | 4       | 7     | 4
6/1/14 5:00 | 3      |         | 7     | 5.
6/1/14 6:00 | 1      | 6       | 7     | 6.0
6/1/14 7:00 | 2      | 7       | 7     | 7
6/1/14 8:00 | 3      |         | 7     | 8.0
6/1/14 9:00 | 1      | 9       | 7     | 9.

Note that test data may include values that are expected to cause problems, or that need special handling by the application.
For example, if the application requires the data to have a non-zero variance, then some column of the input file can have a constant entry.
Similarly, algorithms usually have to be robust against missing values, so some column in the input file may have missing entries.

The columns can be in any order, and the file can contain unused columns.
However, it must include a column of datetime information.

Save the data as a comma-separated-value (CSV) file.


## Expected output

After creating the input data, create one or more files containing the expected output from the application.
Each unit test needs its own file of expected output.
That is, if a single input file contains data for multiple unit tests, each of those tests needs its own expected output file.
If an application will output more than one file, there needs to be respective expected output files.

The file name should follow the pattern `app_name_test_name.ref.csv`.
The `.ref` suffix separates regular output from expected, or _reference_, output.

For example, the expected output for running Daily Summary on the `floats` column of data given above is (square footage was set to 3000 square feet):

Metric                     | value
:--------------------------|:----------
Load Max Intensity         | 0.00233333
Load Min Intensity         | 0.00233333
Daily Load 95th Percentile | 7
Daily Load 5th Percentile  | 7
Daily Load Ratio           | 1
Daily Load Range           | 0
Load Variability           | 0
Peak Load Benchmark        | 2.3333333


## Set up database in OpenEIS

This step creates a database that contains the input data file.

This database will be serialized to a fixture file, so it should be kept as small as possible (i.e, to include only the data needed for the unit tests it will support).
Therefore the existing database should be replaced, rather than simply added to.

Since this step will destroy the existing database, it may be desirable to store its contents for recovery after setting up the test.
To do this, activate the virtual environment, if necessary, then:

    > openeis  dumpdata  >  saved_database.json

Now clear the existing database:

    > openeis  flush

If you wish to create another database, you must create a new super user each time.

Next, run OpenEIS and set up the database as it should exist for testing the application.
*TODO: When available, add hyperlink to user-oriented documentation of setting up the data.*


## Save the database as a fixture

To store the test database, save it as a "fixture":

    > openeis  dumpdata  >  app_name_fixture.json

A fixture is a `JSON`-formatted file containing the contents of the database.
For complete documentation on `dumpdata`, refer to [Django's documentation](https://docs.djangoproject.com/en/1.6/ref/django-admin/#dumpdata-appname-appname-appname-model).

Place the fixture file in the application-level test directory.

An optional step, when creating a fixture file, is to format it "nicely" for viewing.
Here, "nice" mainly means that each top-level JSON object (i.e., each element of the array that is the outer structure of the JSON file) appears on its own line of the file.
This is entirely cosmetic, but it has two advantages when working with the file through a source code repository.
First, it makes the file easier to look at with simple non-JSON-aware editors.
Second, it makes changes to the file easier to identify using line-oriented `diff` tools.

To format the fixture file:

    > python  format-fixture-file.py  <original-file-name>  >  <new-file-name>

Please avoid the mistake of trying to direct the output to a file with the same name as the original.
This is likely to cause problems.

Note `format-fixture-file.py` is in the `utest_applications` subdirectory.


## Restoring a database from a fixture

It may be useful to reload a fixture, in order to reset the database to an earlier state.
For example, after finishing with a test database, it may be desired to restore a working database that was destroyed by a `flush` operation in order to create a database for a unit test.
It may also be helpful to revise the database created for a unit test, say, in order to add to a test.

To install a fixture:

    > openeis  loaddata  saved_database.json

If you only wish to see data in this fixture, you must flush first.
Otherwise you may get an error from the same project ids or sensor map ids mapping to different objects.

If you wish to run a test on multiple fixtures, you must be cautious for this reason.
The ids on different projects will map to different things and thus cause problems.


# Writing a unit test

For each test file, you should create a new class called `TestSomething` and it should extend `AppTestBase`.

`from openeis.applications.utest_applications.apptest import AppTestBase`

This is AppTestBase extends Django's [TestCase](https://docs.djangoproject.com/en/1.6/topics/testing/tools/#django.test.TestCase), and thus enables developers to test with their test framework.
It holds all of the functions and utilities needed to run the tests.
You may wish to read the documentation for existing functions to see if they are of any use to you.


## Testing applications

Each test should have a [configuration file](configuration_file.md).
When writing tests, you may add to the existing `test_applications.py`, which is our own file that contains all the tests, or create your own file.

Either way, when writing tests it should look like the following:

```python
# Only import if you are creating a new file

from openeis.applications.utest_applications.apptest import AppTestBase
import os

class TestYourApplication(AppTestBase):
    fixtures = [os.path.join('applications',
                             'utest_applications',
                             'utest_your_application',
                             'your_application_fixture.json')]

    def test_your_application_test_name(self):
        expected_files = {}
        config_file = os.path.join('applications',
                                       'utest_applications',
                                       'utest_your_application',
                                       'your_application_same_number.ini')
        expected_files['output1'] = os.path.join('applications',
                                       'utest_applications',
                                       'utest_your_application',
                                       'your_application_output1.ref.csv')
        expected_files['output2'] = os.path.join('applications',
                                       'utest_applications',
                                       'utest_your_application',
                                       'your_application_output2.ref.csv')

        self.run_it(config_file, expected_files, clean_up=True)

    def test_your_application_invalid(self):
        config_file = os.path.join('applications',
                               'utest_applications',
                               'utest_your_application',
                               'your_application_invalid.ini')
        self.assertRaises(Exception, self.run_application, config_file)

class TestHeatMap(AppTestBase):
    fixtures = [os.path.join('applications',
                            'utest_applications',
                            'utest_heat_map',
                            'heat_map_fixture.json')]

    def test_heat_map_basic(self):
        hm_basic_exp = {}
        hm_basic_ini = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_basic.ini')
        hm_basic_exp['Heat_Map'] = os.path.join('applications',
                                    'utest_applications',
                                    'utest_heat_map',
                                    'heat_map_basic.ref.csv')
        self.run_it(hm_basic_ini, hm_basic_exp, clean_up=True)
```

In your test class will be the fixtures needed to run the tests as well as all of the tests for that application.
There can more than one test per class and multiple application classes per file.
Put all of the fixtures needed in a list and set equal to "fixtures" at the beginning of the class.

    fixtures = [os.path.join('applications',
                             'utest_applications',
                             'utest_your_application',
                             'your_application_fixture.json')]


This is how Django knows which fixtures to install at the beginning of each test.
Join the paths using `os.path.join` because different operating systems join paths differently.
With this, Python is able to figure out what operating system it is running on and thus how to join the paths correctly.  For documentation, go [here](https://docs.python.org/3.3/library/os.path.html).
Set the `config_file` to the path the of the configuration file made for this test.
The configuration file holds all of the parameters for running the application.  `run_it` will run the application with the configuration file.

    config_file = os.path.join('applications',
                                       'utest_applications',
                                       'utest_your_application',
                                       'your_application_same_number.ini')

To tolerate more than one output file from an application, `expected_files` is a Python dictionary.
Set the key to be the output name and the value to be the file path.
`run_it` will find these files and compare the output of running the application to the expected output.

    expected_files['output1'] = os.path.join('applications',
                                   'utest_applications',
                                   'utest_your_application',
                                   'your_application_output1.ref.csv')
    expected_files['output2'] = os.path.join('applications',
                                   'utest_applications',
                                   'utest_your_application',
                                   'your_application_output2.ref.csv')


Afterwards, call `self.run_it` on the `(config_file, expected_file)`.

    self.run_it(config_file, expected_files, clean_up=True)

A result of calling `run_it` is the output from running the application, which is put into the root directory.
If you do not wish to see the output, set the `clean_up` to "True".


## Testing for exceptions

If you want to test to make sure your application throws an exception under whatever conditions, do the following:

```python
def test_your_application_invalid(self):
    config_file = os.path.join('applications',
                               'utest_applications',
                               'utest_your_application',
                               'your_application_invalid.ini')
    self.assertRaises(Exception, self.run_application, config_file)
```

Make sure the configuration file that is being passed in will make your application throw an exception.
If you are testing for invalid data, make sure that your configuration file uses the invalid dataset.
Use the self.assertRaises function to assert that it raises an exception.
The first argument is what kind of Exception you need it to throw, the second argument is self.run\_application (in utilities), and the third is the configuration file you wish to pass into the application.
This will call the application and assert that it throws a certain exception.

## Utilities

If there are any utilities or external functions that you need for your tests, put them in `testing_utils.py`, located in `applications/utils/`.

## Testing application utilities

If you wish to test utilities that you have created for your application, use the following import.
Make sure that your utilities are in the utils folder of applications.
Test them as you would normal unit tests.
It is best to put the utilities unit together in the `utils` folder.
Remember to import and extend the AppTestBase and import whatever utilities you are testing.

An example of this the test for Spearman Ranks:
```python
from openeis.applications.utest_applications.apptest import AppTestBase
import spearman
import numpy as np

class TestSpearmanRank(AppTestBase):

    # Test ranking
    def test_rank_basic(self):
        row = [1, 2, 3, 4, 5]
        exp_ranks = np.array([1, 2, 3, 4, 5])
        ranks = spearman._rankForSpearman(np.array(row))
        self.nearly_same(ranks, exp_ranks, absTol=1e-18, relTol=1e-12)
```

In this code snippet, we are comparing the ranking algorithm.
`row` refers to the row we will be running our ranking algorithm (_rankForSpearman) on,
and `exp_ranks` refers to what we expect to be the result.
We then compare the two arrays with `nearly_same`, and if they are not nearly the same then the test will fail.
You can look at the documentation for `nearly_same` in AppTestBase.py.


## Running a test

In order to run the test, call:

    > openeis test applications/utest_applications/your_test_file.py

*TODO: If you create your own file, how do you get it to run as part of an automated test suite?
Does Django/OpenEIS "know" to run any .py file it finds in a certain directory?
Do we even know for sure that the tests run automatically at some point on PNL's servers?
Right now, the only time I (DML) know for sure the tests run is if I kick them off explicitly using `openeis test ...`*


## Interpreting test output

Output from a successful test resembles the following:

    nosetests applications/utest_applications/test_applications.py --verbosity=1
    Creating test database for alias 'default'...
    ...................................
    ----------------------------------------------------------------------
    Ran 35 tests in 17.930s

    OK
    Destroying test database for alias 'default'...


Each dot represents a single unit test.
In addition to dots, and `F` or `E` may appear:

+ A dot represents a unit test that passed.
+ `F` stands for "Failed".
+ `E` stands for "Error".

An example of an error is as follows:

    nosetests applications/utest_applications/test_applications.py --verbosity=1
    Creating test database for alias 'default'...
    .............................E.....
    ======================================================================
    ERROR: test_rank_basic (test_applications.TestSpearmanRank)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/openeis/openeis/applications/utest_applications/test_applications.py", line 352, in test_rank_basic
        raise Exception
    Exception
    ----------------------------------------------------------------------
    Ran 35 tests in 18.931s

    FAILED (errors=1)
    Destroying test database for alias 'default'...

If there was an error, you can look at the traceback to see what went wrong.
The output will tell you how many errors there were and which test failed.

If a test failed, it will look like:

    nosetests applications/utest_applications/test_applications.py --verbosity=1
    Creating test database for alias 'default'...
    .......................F............
    ======================================================================
    FAIL: example_test (test_applications.TestSpearmanRank)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/openeis/openeis/applications/utest_applications/test_applications.py", line 348, in example_test
        self.assertTrue(False)
    AssertionError: False is not true
    ----------------------------------------------------------------------
    Ran 36 tests in 21.822s

    FAILED (failures=1)
    Destroying test database for alias 'default'...

Similar to the error, `nose` will give a traceback to the failure, which test failed, and how many tests failed.
