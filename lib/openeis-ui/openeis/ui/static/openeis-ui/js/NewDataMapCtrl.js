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
.controller('NewDataMapCtrl', function ($location, $scope, project, dataFiles, DataMaps, DataSets, Modals, newDataMap) {
    $scope.project = project;
    $scope.dataFiles = dataFiles;
    $scope.Modals = Modals;
    $scope.isObject = angular.isObject;

    DataMaps.ensureFileMetaData($scope.dataFiles);

    $scope.newDataMap = newDataMap;

    $scope.$on('$locationChangeStart', function (event) {
        if ($scope.newDataMap.map.children.length && !confirm('Abandon unsaved data map?')) {
            event.preventDefault();
        }
    });

    $scope.$watch('newDataMap.map', function () {
        DataMaps.validateMap($scope.newDataMap.map)
            .then(function (result) {
                $scope.newDataMap.valid = result.valid;
            });
    }, true);

    $scope.addChild = function (childLevel) {
        var name,
            promptMessage = 'Name:',
            hasName = function (element) {
                return (element.name === name);
            };

        do {
            name = prompt(promptMessage);
            if (!name) { return; }
            name = name.replace('/', '-');
            promptMessage = 'Error: "' + name + '" already exists. Name:';
        } while ($scope.newDataMap.map.children.some(hasName));

        $scope.newDataMap.map.children.unshift({
            level: childLevel,
            name: name,
        });
    };

    $scope.preview = function () {
        var files = [],
            filesMap = {},
            fileCounter = 0;

        function getFiles(objects) {
            angular.forEach(objects, function (object) {
                if (object.deleted === true) {
                    return;
                }

                if (object.file) {
                    if (!filesMap[object.file.id]) {
                        filesMap[object.file.id] = {
                            key: fileCounter++ + '',
                            name: object.file.name,
                        };
                    }
                }

                if (object.sensors) { getFiles(object.sensors); }
                if (object.children) { getFiles(object.children); }
            });
        }

        getFiles($scope.newDataMap.map.children);

        $scope.dataMapPreviewFiles = {};

        angular.forEach(filesMap, function (values, fileId) {
            files.push({ name: values.key, file: fileId });
            $scope.dataMapPreviewFiles[values.key] = values.name;
        });

        DataSets.preview(DataMaps.flattenMap($scope.newDataMap.map), files).$promise.then(function (dataMapPreview) {
            $scope.dataMapPreview = dataMapPreview;
            Modals.openModal('dataMapPreview');
        });
    };

    $scope.showError = function (error) {
        alert([
            $scope.dataMapPreviewFiles[error.file],
            ': row ',
            error.row,
            ', column ',
            error.column,
            '\n',
            error.error
        ].join(''));
    };

    $scope.save = function () {
        DataMaps.create($scope.newDataMap).$promise.then(function () {
            // Clear children so we don't trigger confirmation
            $scope.newDataMap.map.children = [];
            $location.url('projects/' + project.id);
        }, function (rejection) {
            alert(rejection.data.__all__.join('\n'));
        });
    };
});
