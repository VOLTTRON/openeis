from openeis.projects import models


def clone_project(project, new_project_name):
    ''' Clones project. Copies existing project and save with new name. 
        Copies sensor map, sensor ingest, sensors and analyses from existing project to cloned project.
    '''
    sensor_maps = models.SensorMapDefinition.objects.filter(project=project)
    #data_files = models.DataFile.objects.filter(project=project)
    
    project.id = None
    project.name = new_project_name
    project.save()
    
    #clone_data_files(list(data_files), project)
    clone_sensor_map_definition(list(sensor_maps), project)
        
    return project

def clone_data_files(data_files_list, project):
    for data_file in data_files_list:
        data_file.id = None
        data_file.save()

def clone_sensor_map_definition(sensor_maps_list,project):
    for sensor_map in sensor_maps_list:
        
        sensor_ingests = models.SensorIngest.objects.filter(map=sensor_map)
        sensors = models.Sensor.objects.filter(map=sensor_map)
        
        sensor_map.id = None
        sensor_map.project = project
        sensor_map.save()
        
        clone_sensor_ingest(list(sensor_ingests),sensor_map)
        clone_sensors(list(sensors), sensor_map)

def clone_sensor_ingest(sensor_ingests_list, sensor_map_definition):
    for sensor_ingest in sensor_ingests_list:
        
        analyses = models.Analysis.objects.filter(dataset=sensor_ingest)
        
        sensor_ingest.id = None
        sensor_ingest.map = sensor_map_definition
        sensor_ingest.save()
        
        clone_analysis(list(analyses), sensor_ingest)
        
def clone_sensors(sensors_list, sensor_map):
    for sensor in sensors_list:
        sensor.id= None
        sensor.map = sensor_map
        sensor.save()

def clone_analysis(analyses_list, sensor_ingest):
    for analysis in analyses_list:
        analysis.id= None
        analysis.dataset = sensor_ingest
        analysis.save()