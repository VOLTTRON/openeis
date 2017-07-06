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

angular.module('openeis-ui.directives.sensor-container', [
    'RecursionHelper',
    'openeis-ui.components.modals',
    'openeis-ui.filters',
    'openeis-ui.services.data-maps',
])
.directive('sensorContainer', function (RecursionHelper) {
    return {
        restrict: 'E',
        scope: {
            container: '=',
            files: '=',
            parent: '=',
        },
        templateUrl: 'sensor-container-directive.tpl.html',
        controller: function ($scope, DataMaps, Modals) {
            DataMaps.getDefinition().then(function (definition) {
                $scope.definition = definition;

                $scope.objectDefinition = definition[$scope.container.level];

                if ($scope.objectDefinition.sensor_list) {
                    if ($scope.objectDefinition.sensor_list === '*') {
                        $scope.objectDefinition.sensor_list = [];
                        angular.forEach(definition.sensors, function (def, name) {
                            $scope.objectDefinition.sensor_list.push(name);
                        });
                    }

                    $scope.objectDefinition.sensor_list.sort();
                }

                if ($scope.objectDefinition.attribute_list) {
                    if ($scope.objectDefinition.attribute_list === '*') {
                        $scope.objectDefinition.attribute_list = [];
                        angular.forEach(definition.attributes, function (def, name) {
                            $scope.objectDefinition.attribute_list.push(name);
                        });
                    }

                    // Time zone is only allowed on top-level objects
                    if (!$scope.parent.hasOwnProperty('version') && $scope.objectDefinition.attribute_list.indexOf('timezone') >  -1) {
                        $scope.objectDefinition.attribute_list.splice($scope.objectDefinition.attribute_list.indexOf('timezone'), 1);
                    }

                    $scope.objectDefinition.attribute_list.sort();
                }
            });

            DataMaps.getUnits().then(function (units) {
                $scope.units = units;
            });

            $scope.rename = function () {
                var name,
                    promptMessage = 'Name:',
                    hasName = function (element) {
                        return (element.name === name);
                    };

                do {
                    name = prompt(promptMessage);
                    if (!name || name === $scope.container.name) { return; }
                    name = name.replace('/', '-');
                    promptMessage = 'Error: "' + name + '" already exists. Name:';
                } while ($scope.parent.children.some(hasName));

                $scope.container.name = name;
            };

            $scope.prompt = function (action) {
                Modals.openModal(action + '-' + $scope.container.$$hashKey);
            };

            $scope.cancel = function (action) {
                $scope[action] = {};
                Modals.closeModal(action + '-' + $scope.container.$$hashKey);
            };

            $scope.newAttribute = {};

            $scope.showAttribute = function (attributeName) {
                return !($scope.container.attributes && $scope.container.attributes[attributeName]);
            };

            $scope.addAttribute = function () {
                $scope.container.attributes = $scope.container.attributes || {};
                $scope.container.attributes[$scope.newAttribute.name] = $scope.newAttribute.value;
                $scope.cancel('newAttribute');
            };

            $scope.deleteAttribute = function (attribute) {
                delete $scope.container.attributes[attribute];

                if (!Object.keys($scope.container.attributes).length) {
                    delete $scope.container.attributes;
                }
            };

            $scope.newSensor = {};

            $scope.$watchCollection('newSensor', function () {
                if (!$scope.newSensor.file || !$scope.newSensor.file.columns[$scope.newSensor.column]) {
                    $scope.newSensor.column = '';
                }

                if (!$scope.newSensor.name ||
                    !$scope.units[$scope.definition.sensors[$scope.newSensor.name].unit_type] ||
                    !$scope.units[$scope.definition.sensors[$scope.newSensor.name].unit_type][$scope.newSensor.unit]) {
                    delete $scope.newSensor.unit;
                }
            });

            $scope.showSensor = function (sensorName) {
                var alreadyAdded = false;

                angular.forEach($scope.container.sensors, function (addedSensor) {
                    if (!alreadyAdded && addedSensor.type === sensorName) {
                        alreadyAdded = true;
                    }
                });

                return !alreadyAdded;
            };

            $scope.addSensor = function () {
                $scope.newSensor.type = $scope.newSensor.name;
                $scope.container.sensors = $scope.container.sensors || [];
                $scope.container.sensors.unshift(angular.copy($scope.newSensor));
                $scope.cancel('newSensor');
            };

            $scope.deleteSensor = function (index) {
                $scope.container.sensors.splice(index, 1);
            };

            $scope.addChild = function (childLevel) {
                var name,
                    promptMessage = 'Name:',
                    hasName = function (element) {
                        return (element.name === name);
                    };

                $scope.container.children = $scope.container.children || [];

                do {
                    name = prompt(promptMessage);
                    if (!name) { return; }
                    name = name.replace('/', '-');
                    promptMessage = 'Error: ' + $scope.container.name + 'already has child "' + name + '". Name:';
                } while ($scope.container.children.some(hasName));

                $scope.container.children.unshift({
                    level: childLevel,
                    name: name,
                });
            };
        },
        compile: function(element) {
            return RecursionHelper.compile(element);
        },
    };
});
