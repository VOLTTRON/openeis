// Copyright (c) 2014, Battelle Memorial Institute
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
// ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
// The views and conclusions contained in the software and documentation are those
// of the authors and should not be interpreted as representing official policies,
// either expressed or implied, of the FreeBSD Project.
//
//
// This material was prepared as an account of work sponsored by an
// agency of the United States Government.  Neither the United States
// Government nor the United States Department of Energy, nor Battelle,
// nor any of their employees, nor any jurisdiction or organization
// that has cooperated in the development of these materials, makes
// any warranty, express or implied, or assumes any legal liability
// or responsibility for the accuracy, completeness, or usefulness or
// any information, apparatus, product, software, or process disclosed,
// or represents that its use would not infringe privately owned rights.
//
// Reference herein to any specific commercial product, process, or
// service by trade name, trademark, manufacturer, or otherwise does
// not necessarily constitute or imply its endorsement, recommendation,
// or favoring by the United States Government or any agency thereof,
// or Battelle Memorial Institute. The views and opinions of authors
// expressed herein do not necessarily state or reflect those of the
// United States Government or any agency thereof.
//
// PACIFIC NORTHWEST NATIONAL LABORATORY
// operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
// under Contract DE-AC05-76RL01830

angular.module('openeis-ui.services.data-maps', [
    'ngResource',
    'openeis-ui.services.data-files',
])
.service('DataMaps', function ($http, $q, $resource, DataFiles) {
    var DataMaps = this,
        resource = $resource(settings.API_URL + 'datamaps/:mapId', { mapId: '@id' }, {
            create: { method: 'POST' },
            save: { method: 'PUT' },
        });

    DataMaps.get = function (mapId) {
        return resource.get({ mapId: mapId });
    };

    DataMaps.query = function (projectId) {
        return resource.query({ project: projectId });
    };

    DataMaps.create = function (dataMap) {
        var copy = angular.copy(dataMap);
        copy.map = DataMaps.flattenMap(copy.map);
        return resource.create(copy);
    };

    DataMaps.getDefaultMap = function (projectId) {
        return {
            project: projectId,
            map: {
                version: 1,
                children: [{
                    level: 'building',
                    name: 'New building',
                }],
            },
            valid: false,
        };
    };

    DataMaps.getDefinition = function () {
        return $http.get(settings.GENERAL_DEFINITION_URL).then(function (response) {
            return response.data;
        });
    };

    DataMaps.getUnits = function () {
        return $http.get(settings.UNITS_URL).then(function (response) {
            return response.data;
        });
    };

    DataMaps.flattenMap = function (map) {
        var mapCopy = angular.copy(map),
            files = {},
            fileCounter = 0;

        function flattenObject(objects, topicBase) {
            var flattened = {};

            angular.forEach(objects, function(object) {
                if (object.deleted === true) {
                    return;
                }

                delete object.deleted;

                var topic = topicBase + object.name.replace('/', '-'),
                    sensors = object.sensors || {},
                    children = object.children || {};

                delete object.name;
                delete object.sensors;
                delete object.children;

                if (object.file) {
                    if (object.file.hasHeader) {
                        object.column = object.file.columns[parseInt(object.column)];
                    } else {
                        object.column = parseInt(object.column);
                    }

                    if (!files[object.file.name]) {
                        files[object.file.name] = {
                            key: fileCounter++ + '',
                            signature: object.file.signature,
                            timestamp: object.file.timestamp,
                        };
                    }

                    object.file = files[object.file.name].key;
                }

                flattened[topic] = object;

                angular.extend(flattened, flattenObject(sensors, topic + settings.DATAMAP_TOPIC_SEPARATOR));
                angular.extend(flattened, flattenObject(children, topic + settings.DATAMAP_TOPIC_SEPARATOR));
            });

            return flattened;
        }

        mapCopy.sensors = flattenObject(mapCopy.children, '');

        delete mapCopy.children;

        mapCopy.files = mapCopy.files || {};

        angular.forEach(files, function (file, key) {
            mapCopy.files[file.key] = file;
            delete mapCopy.files[file.key].key;
        });

        return mapCopy;
    };

    DataMaps.unFlattenMap = function (dataMap, dataFiles) {
        var topics = Object.getOwnPropertyNames(dataMap.map.sensors).sort();

        // Reverse map signatures to available files
        angular.forEach(dataMap.map.files, function (file, key) {
            angular.forEach(dataFiles, function (dataFile) {
                if (angular.equals(file.signature, dataFile.signature) && angular.equals(file.timestamp, dataFile.timestamp)) {
                    dataMap.map.files[key] = dataFile;
                }
            });
        });

        dataMap.map.children = [];

        angular.forEach(topics, function (topic) {
            var mapObject = dataMap.map.sensors[topic],
                topicParts = topic.split('/'),
                parent = dataMap.map;

            function childIsNewParent(child) {
                if (child.name === topicPart) {
                    parent = child;
                }
            }

            while (topicParts.length > 1) {
                var topicPart = topicParts.shift();

                angular.forEach(parent.children, childIsNewParent);
            }

            mapObject.name = topicParts[0];

            if (mapObject.level) {
                // object is a container
                mapObject.children = [];
                mapObject.sensors = [];
                parent.children.push(mapObject);
            } else if (mapObject.type) {
                // object is a sensor
                if (dataMap.map.files[mapObject.file].name) {
                    // If file with matching signature was found, file object will have a name
                    mapObject.file = dataMap.map.files[mapObject.file];

                    if (mapObject.file.hasHeader) {
                        mapObject.column = mapObject.file.columns.indexOf(mapObject.column);
                    }
                } else {
                    mapObject.file = {
                        name: 'MISSING FILE',
                        columns: {},
                    };

                    mapObject.file.columns[mapObject.column] = 'MISSING COLUMN';
                }

                parent.sensors.push(mapObject);
            }
        });

        delete dataMap.id;
        delete dataMap.map.files;
        delete dataMap.map.sensors;

        dataMap.name += ' copy';

        return dataMap;
    };

    DataMaps.validateMap = function (map) {
        return $http.get(settings.DATAMAP_SCHEMA_URL)
            .then(function (response) {
                return tv4.validateMultiple(DataMaps.flattenMap(map), response.data);
            });
    };

    DataMaps.ensureFileMetaData = function (files) {
        var promises = [];

        angular.forEach(files, function(file) {
            if (!(file.hasOwnProperty('signature') && file.hasOwnProperty('columns') && file.hasOwnProperty('hasHeader'))) {
                promises.push(DataFiles.head(file.id).then(function (headResponse) {
                    file.signature = { headers: [] };
                    file.columns = [];
                    file.hasHeader = headResponse.has_header;

                    angular.forEach(headResponse.rows[0], function (v, k) {
                        if (file.hasHeader) {
                            file.signature.headers.push(v);
                            file.columns.push(v);
                        } else {
                            file.signature.headers.push(null);
                            file.columns.push("Column " + (k + 1));
                        }
                    });
                }));
            }
        });

        return $q.all(promises);
    };
});
