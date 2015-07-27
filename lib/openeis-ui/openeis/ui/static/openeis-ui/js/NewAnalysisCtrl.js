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

angular.module('openeis-ui')
.controller('NewAnalysisCtrl', function ($scope, Applications, DataMaps, $q, Modals, Analyses) {
    $scope.newAnalysis = { debug: false };

    $scope.$watch('newAnalysis.dataSet', function () {
        $scope.availableApps = [];

        if (!$scope.newAnalysis.dataSet) {
            return;
        }

        // Data set has been selected, generate lists of available and required sensors
        // and compare for compatibility
        Applications.query().$promise.then(function (apps) {
            $scope.availableSensors = {};

            angular.forEach($scope.newAnalysis.dataSet.datamap.sensors, function (sensor, topic) {
                if (!sensor.type) {
                    return;
                }

                if (!$scope.availableSensors.hasOwnProperty(sensor.type)) {
                    $scope.availableSensors[sensor.type] = [];
                }

                $scope.availableSensors[sensor.type].push(topic);
            });

            angular.forEach(apps, function (app) {
                var requiredCounts = {},
                    missingInputs = [];

                app.name = app.name || app.id;

                angular.forEach(app.inputs, function (input) {
                    if (!requiredCounts.hasOwnProperty(input.sensor_type)) {
                        requiredCounts[input.sensor_type] = 0;
                    }

                    requiredCounts[input.sensor_type] += input.count_min;
                });

                angular.forEach(requiredCounts, function (required, sensorType) {
                    var available = 0;

                    if ($scope.availableSensors[sensorType]) {
                        available = $scope.availableSensors[sensorType].length;
                    }

                    if (available < required) {
                        missingInputs.push(
                            'At least ' + required + ' ' + sensorType + ' required, ' + available + ' available in data set'
                        );
                    }
                });

                if (missingInputs.length) {
                    $scope.availableApps.push({
                        name: app.name,
                        description: app.description,
                        missingInputs: missingInputs,
                    });
                    return;
                }

                $scope.availableApps.push(app);
            });
        });
    });

    var previousApp;

    $scope.$watch('newAnalysis.application', function (newValue, oldValue) {
        // Reset configuration if application has changed
        if (newValue && newValue !== previousApp) {
            $scope.newAnalysis.configuration = { parameters: {}, inputs: {} };

            // Initialize multi-sensor inputs
            angular.forEach(newValue.inputs, function (input, inputName) {
                $scope.newAnalysis.configuration.inputs[inputName] = [];

                var i = 0;
                while (i++ < input.count_min) {
                    $scope.newAnalysis.configuration.inputs[inputName].push({});
                }
            });

            previousApp = newValue;
        }
    });

    $scope.setParamDefault = function (paramName) {
        if ($scope.newAnalysis.application.parameters[paramName].hasOwnProperty('value_default')) {
            $scope.newAnalysis.configuration.parameters[paramName] = $scope.newAnalysis.application.parameters[paramName].value_default;
        }
    };

    $scope.canAddSensor = function (inputName, inputType) {
        var app = $scope.newAnalysis.application,
            config = $scope.newAnalysis.configuration;

        if (!$scope.availableSensors[inputType]) {
            return false;
        }

        if (config.inputs[inputName].length >= $scope.availableSensors[inputType].length) {
            return false;
        }

        if (app.inputs[inputName].count_max && config.inputs[inputName].length >= app.inputs[inputName].count_max) {
            return false;
        }

        return true;
    };

    $scope.addInputSensor = function (inputName) {
        $scope.newAnalysis.configuration.inputs[inputName].push({});
    };

    $scope.deleteInputSensor = function (inputName, index) {
        $scope.newAnalysis.configuration.inputs[inputName].splice(index, 1);
    };

    $scope.run = function () {
        Analyses.create({
            name: $scope.newAnalysis.dataSet.name + ' - ' + $scope.newAnalysis.application.name,
            dataset: $scope.newAnalysis.dataSet.id,
            application: $scope.newAnalysis.application.id,
            configuration: $scope.newAnalysis.configuration,
            debug: $scope.newAnalysis.debug,
        }).$promise.then(function (analysis) {
            $scope.analyses.push(analysis);
            $scope.statusCheck();
            Modals.closeModal('newAnalysis');
        }, function (rejection) {
            alert(angular.toJson(rejection.data, true));
        });

    };
});
