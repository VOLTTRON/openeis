# Creating configuration files
Configuration files are passed in as parameters when you run your application.
It contains the metadata for the building and sensor maps used in the application.
To run your application call refer to the [command line basics](command_line_basics_unix.md).
Your configuration file ends with ".ini" to indicate that it is a configuration file.
Your files should look like the following:

    [global_settings]
    application=your_application
    dataset_id=1 [respective dataset_id]
    sensormap_id=1 [respective sensormap_id]

    [application_config]
    building_sq_ft=3000 [if needed]
    building_name="testbuilding" [if needed]

    [inputs]
    load=testsite/testbuilding/WholeBuildingElectricity
    natgas=testsite/testbuilding/AnyOtherSensorYouMayNeed

Under `global_settings`, you should write what application you plan on running as well as the dataset and sensor map respective IDs.
The dataset_id and sensormap_id refers to the datasets and sensor maps you have created in your database.
For more information on how to create these, refer to the [basic use](example.net) or to the [api page](server_api_tricks.md).
The id numbering starts at 1 and goes on from there so first data set's and sensor map's id is 1.
If you are unsure of which dataset and which sensor map to use,
refer to the [sensor map api page](http://localhost:8000/api/sensormaps) and the [analysis api page](http://localhost:8000/api/analyses) for datasets to see.
Under `application_config` are any configuration details you need to add for your application such as the square footage or building name.
The `inputs` are the parameters needed from the data files for your application to run such as outdoor air temperature or whole building electricity.


