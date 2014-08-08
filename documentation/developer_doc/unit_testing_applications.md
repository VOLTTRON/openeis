# OpenEIS Unit Testing Applications Guide


## Introduction

This section describes creating and running unit tests for applications hosted under OpenEIS.

Each test of an application comprises an input data file, configuration file, a sensor map, a dataset, and expected output.

The tests use Python's `nose` unit testing framework included in [Django's testing framework](https://docs.djangoproject.com/en/1.6/topics/testing/).


## Overview

The unit tests have three main concerns:

+ Setting up the data the application needs to run.
  This includes everything the application normally would acquire from the User Interface: the configuration parameters as well as the raw data.
+ Invoking a run of the application.
+ Retrieving the output, and checking against the expected results.
  Note that "expected results" can include verifying that feed an application bad data causes it to fail in a controlled way, as well as checking that it computes the correct results for good data.

Each application can have multiple individual tests.
*TODO: Need to settle on, and define, terms to refer to the tests.
For example, does "unit test" refer to the whole suite of tests that can run against a single application?
Or to an individual test?
In any case, need terms to distinguish between these, and need to make sure to use those terms consistently throughout this document.
For the rest of the comments below, I'll refer to _individual_ and _application-level_ unit tests, but there may be better terms than this.*


*TODO: Need to finish this overview of the workflow, getting into a little detail about how each piece described below contributes to the workflow.*


## Test directory

Create a new subdirectory in

    openeis_root/openeis/applications/utest_applications

where `openeis_root` is the root directory that contains the OpenEIS project files.
Note that the examples given here use a Unix-style forward slash (`/`) as the file path separator.
On Windows machines, use a DOS-style backward slash (`\`).

The new subdirectory will contain all the required files for testing the application.
These include data files, configuration files, and expected output files.

For an application called `my_app_name`, the suggested test subdirectory is

    openeis_root/openeis/applications/utest_applications/my_app_name


## Input data file

Create a file that contains the sample data against which the application will be run.
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

Note that test data may include values that are expected to cause problems, or that need special handling.
For example, if the application requires the data to have a non-zero variance, then some column of the input file can have a constant entry.
Similarly, algorithms usually have to be robust against missing values, so some column in the input file may have missing entries.

The columns can be in any order, and the table can have enough data to support multiple individual tests.
However, the file must include a column of datetime information.

Save the data as a comma-separated-value (CSV) file.


## Expected output file

After creating the input data, create a file containing the expected output from the application.
The file name should follow the pattern `application_name_test_type.ref.csv`.
The `.ref` suffix separates regular output from expected, or _reference_, output.

For example, the expected output for running Daily Summary on the `floats` column of data given above is:
*TODO: For what value of `building_sq_ft`?*

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

*TODO: Need to make clear that the file, and the file name, relates to the individual unit tests.*


## Set up database in OpenEIS

This step creates a database that contains the input data file.

This database will be serialized to a fixture file, so it should be kept as small as possible (i.e, to include only the data needed for the unit test.
Therefore the first step is to remove all information from the existing database.
Activate the virtual environment, if necessary, then

    > openeis  flush

*TODO: Is there an easier way, that doesn't require you to set up a new superuser and so on?*

*TODO: Maybe suggest preserving the current database as a fixture, and then restoring it later with `loaddata`?*

*TODO: When available, add hyperlink to user-oriented documentation of setting up the data.*




## Creating a fixture

Now we want to save the state of this database as is.
Django provides a function `dumpdata` that will store the data as a "fixture".
A fixture is a `JSON`-formatted file containing the contents of the database.
For complete documentation on this command, refer to [Django's documentation](https://docs.djangoproject.com/en/1.6/ref/django-admin/#dumpdata-appname-appname-appname-model).

    > openeis  dumpdata  >  path/to/your_application_fixture.json

Place this file in the directory made earlier.

An optional step, when creating a fixture file, is to format it "nicely" for viewing.
Here, "nice" mainly means that each major JSON object appears on its own line of the file.
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
For example, this may be helpful in order to revise the database created for a unit test, say, in order to add to a test.
It may also be helpful to restore a working database that was destroyed by a `flush` operation in order to create a database for a unit test.

To install a fixture:

    > openeis  loaddata  path/to/your_application_fixture.json

*TODO: Is it necessary to flush first, or will this automatically remove anything that's already in there?*


## Writing the tests

We use Django's testing framework.
For each test, Django flushes the database, installs your fixture as shown above, and tears it down after the test is done.
It does this for every test, thus creating an isolated environment for each test.
As a result, the tests should not depend on each other.
Furthermore the tests are executed in no particular order when the tests are run.


## Utilities

If there are any utilities or external functions that you need for your tests, put them in `apptest.py`, located in `applications/utest_applications/`.
This class extends Django's test case, and is thus the test base for our tests.
It holds all of the functions and utilities needed to run the tests.
For example, if your test requires finding the mean of a set up numbers, a function that naively calculates the mean is in AppTestBase.
Your test will extend the class AppTestBase.
You may wish to read the documentation for existing functions to see if they are of any use to you.

If for some reason, your application uses a utility or external function that cannot be placed in AppTestBase, simply import as you would any other module.


## Testing application output equality

Each test should have a [configuration file](configuration_file.md).
When writing tests, you may add to the existing `test_applications.py`, which is our own file that contains all the tests, or create your own file.
Either way, when writing tests it should look like the following (use `test_applications.py` as a reference).

```python
# Only import if you are creating a new file.

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

For each application you are testing, you should create a new class called `TestYourApplication` and it should extend `AppTestBase`.
In this class will be the fixtures needed to run the tests as well as all of the tests for that application.
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


## Running the tests

In order to run the test, simply call:

    > openeis test applications/utest_applications/your_test_file.py


## Reading the output

If your tests ran successfully, it should read the following:

    nosetests applications/utest_applications/test_applications.py --verbosity=1
    Creating test database for alias 'default'...
    ...................................
    ----------------------------------------------------------------------
    Ran 35 tests in 17.930s

    OK
    Destroying test database for alias 'default'...


Each dot represents a single test.
It will either be a dot, F, or E.
Dot means that your test has passed.
F stands for "Failed."
E stands for "Error."

An example of an error is as follows:

    nosetests applications/utest_applications/test_applications.py --verbosity=1
    Creating test database for alias 'default'...
    .............................E.....
    ======================================================================
    ERROR: test_rank_basic (test_applications.TestSpearmanRank)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/Users/vivdawg/workThings/openeis/openeis/applications/utest_applications/
    test_applications.py", line 352, in test_rank_basic
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
      File "/Users/vivdawg/workThings/openeis/openeis/applications/utest_applications/
    test_applications.py", line 348, in example_test
        self.assertTrue(False)
    AssertionError: False is not true
    ----------------------------------------------------------------------
    Ran 36 tests in 21.822s

    FAILED (failures=1)
    Destroying test database for alias 'default'...

Similar to the error, `nose` will give you a traceback to the failure, which test failed, and how many tests failed.
