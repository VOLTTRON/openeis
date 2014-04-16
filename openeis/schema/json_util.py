import csv
import json


input_file = open("input.csv", "r")
# field_names = (sensor object    Type    Customizable Name    Unit    Minimum    Maximum
input_csv = csv.DictReader(input_file, delimiter='\t')
output_file = open("sensor_data.json", "w")
sensors_dict = {}
for row in input_csv:
    s_type = row["sensor_type"]
    sensors_dict[s_type] = row
    
output_file.write(json.dumps(sensors_dict, sort_keys=True,
                  indent=4, separators=(',', ': ')))



