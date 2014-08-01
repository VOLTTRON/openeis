# OpenEIS Unit Testing Applications Guide


## Introduction
This section describes creating and running unit tests for applications hosted under OpenEIS.

Each test of an application comprises an input data file, configuration file, a sensor map, a dataset, and expected output.

*TODO: Add hyperlinks to appropriate subsections.
Maybe put into a bullet list as well.
Note: internal hyperlinks apparently are not supported by Mercurial, but should be by GitHub (judging from their respective documentation).*

The tests use Python's `nose` unit testing framework.

*TODO: Add hyperlink to nose documentation.*

*TODO: Need to provide an overview of the workflow, and what each piece is doing in the workflow.
Goal is to address the complaints, below, about lack of context.*


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
For example, if the application requires the data to have a nonzero variance, then some column of the input file can have a constant entry.
Similarly, algorithms usually have to be robust against missing values, so some column in the input file may have missing entries.

The columns can be in any order, and the table can have enough data to support multiple individual tests.
However, the file must include a column of datetime information.

Save the data as a comma-separated-value (CSV) file.


## Expected output file

After creating the input data, create a file containing the expected output from the application.
The file name should follow the pattern `application_name_test_type.ref.csv`.
The `.ref` suffix separates regular output from expected, or _reference_, output.

For example:

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

*TODO: These numbers might have to change, since I (DML) changed the count of data in the column they apparently came from.
Or was there a connection?*


## Set up database in OpenEIS

*TODO: Need information on how to do this.*


## Creating a fixture

Now we want to save the state of this database as is.
Django provides a function `dumpdata` that will store the data as a "fixture".
A fixture is a `JSON`-formatted file containing the contents of the database.
For complete documentation on this command, refer to [Django's documentation][DjangoDocsFixture].

    > openeis  dumpdata  >  your_application_fixture.json

Place this file in the directory made earlier.

*TODO: Mention formatting a fixture file, which makes it easier to view, and easier to keep under version control.*


## Revising a fixture

Suppose you want to change something in the database used for a unit test.
You can install a fixture, edit it, and then call `dumpdata` again.

To install a fixture:

    > openeis  loaddata  path/to/your_application_fixture.json


## Writing the tests

We use Django's testing framework, which flushes the database, installs your fixture as shown above, and tears it down after the test is done.
It does this for every test, thus creating an isolated environment for each test.
As a result, the tests should not depend on each other.
Furthermore the tests are executed in no particular order when it is run.

*TODO: This needs more context, regarding the distinction between "individual tests".
Does the order of the tests mentioned above mean the order of fixtures?
Or the order of the tests supported by a single fixture?
Probably should move the paragraph above to appear earlier in this documentation, and expand it to give a preview of how individual tests will be created.*


## Utilities

If there are any utilities or external functions that you need, put them in `apptest.py`.
This is a class that holds all of the functions and utilities for the tests.
Your test will extend the class AppTestBase.
You may wish to read the documentation for existing functions to see if they are of any use to you.

*TODO: Again, need more context here.
List directory where apptest.py resides.
Describe what it does before start talking about utilities (or else describe utilities in context of a subsection talking about what apptest does).*

*TODO: If a particular application has specialized needs for a utility or external function, can't that be placed in a class that derives from apptest.pty?*

*TODO: Can apptest.py just be the Python init file for that directory?*


## Testing application output equality

Each test should have a [configuration file](http://example.net/).
When writing tests, you may add to the existing `test_applications.py` or create your own file.
Either way, when writing tests it should look like the following (use `test_applications.py` as a reference).

*TODO: Still need some context.
Should have already described what `test_applications.py` is and does.*

*TODO: Fill in link to configuration file page, once it's created.*

    # Only import if you're creating a new file.

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

For each application you're testing, you should create a new class called `TestYourApplication` and it should extend `AppTestBase`.
In this class will be the fixtures needed to run the tests as well as all of the tests for that application.
Put all of the fixtures needed in a list and set equal to "fixtures" at the beginning of the class.
Make sure to join the path using `os.path.join`.
Set the `config_file` to the path the of the configuration file made for this test.
To tolerate more than one output file from an application, `expected_files` is a Python dictionary.
Set the key to be the output name and the value to be the file path.
Afterwards, call `self.run_it` on the `(config_file, expected_file)`.
The `clean_up` option is if you wish to keep the outputs created from calling the application.
This is automatically set to false, but you may wish to delete the files by setting it equal to True.

*TODO: Show sample code blocks.
Vague descriptions like "Make sure to join the path using os.path.join" and "Set the config file" and "the clean up option" don't help, because there's no context of why you are joining any paths, or how you are setting the config file, or how or when you invoke the clean up option.*

*TODO: Consider putting the finer points listed in the para above, into a bullet list.*

*TODO: Need to tweak the organization here (either break up into multiple subsections, or rename this subsection).
Most of this subsection seems to relate to how you set up the test, not how you test for output equality.*


## Testing for exceptions

If you want to test to make sure your application throws an exception under whatever conditions, do the following:

    def test_your_application_invalid(self):
        config_file = os.path.join('applications',
                                   'utest_applications',
                                   'utest_your_application',
                                   'your_application_invalid.ini')
        self.assertRaises(Exception, self.run_application, config_file)

*TODO: In GitHub-flavored markdown, and in Markdown as supported by BitBucket, can put code blocks in triple backticks, and supply the name of the language.
This will provide syntax highlighting.*

Make sure the configuration file that is being passed in will make your application throw an exception.
Use the self.assertRaises function to assert that it raises an exception.  The first argument is what kind of Exception you need it to throw, the second argument is self.run\_application (in utilities), and the third is the configuration file you wish to pass into the application.  This will call the application and assert that it throws a certain exception.

*TODO: "The configuration file that is being passed in" needs context.
Also, does the configuration file cause an exception, or do the data specified by the config file cause the exception?
The unit tests should be catching problems in the application, not in the configuration of the application run (which is a platform concern).*


## Testing application utilties

If you wish to test utilities that you have created for your application, use the following import.
Make sure that your utilites are in the utils folder of applications.
Test them as you would normal unit tests.

    from openeis.applications.utils import your_utils

*TODO: Need context.
Where do you add this line?
None of this makes any sense unless you are looking at the files already provided.*


## Running the tests

In order to run the test, simply call:

    > openeis test applications/utest_applications/your_test_file.py

*TODO: Somewhere need to give a reference to how you create multiple tests for a single application.
Probably as part of the highest-level overview block, summarizing the overall process.*


## Reading your output

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

[DjangoDocsFixture]: https://docs.djangoproject.com/en/1.6/ref/django-admin/
