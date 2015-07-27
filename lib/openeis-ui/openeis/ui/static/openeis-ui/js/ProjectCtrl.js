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
.controller('ProjectCtrl', function ($scope, project, dataFiles, DataFiles, dataSets, DataSets, dataMaps, $upload, $timeout, $q, $http, Modals, analyses, Analyses, sharedAnalyses, SharedAnalyses) {
    $scope.project = project;
    $scope.dataFiles = dataFiles;
    $scope.dataSets = dataSets;
    $scope.dataMaps = dataMaps;
    $scope.Modals = Modals;
    $scope.analyses = analyses;
    $scope.sharedAnalyses = sharedAnalyses;

    var statusCheckPromise;

    $scope.statusCheck = function () {
        angular.forEach($scope.dataSets, function (dataSet) {
            if (!dataSet.status || dataSet.status.status.slice(-8) !== 'complete') {
                var promises = [];

                promises.push(DataSets.getStatus(dataSet).then(function (response) {
                    dataSet.status = response.data;

                    if (dataSet.status.status === 'processing') {
                        dataSet.status.status += ' - ' + Math.floor(parseFloat(dataSet.status.percent)) + '%';
                    }
                }));

                promises.push(DataSets.getErrors(dataSet).then(function (response) {
                    dataSet.errors = response.data;
                }));

                $q.all(promises).then(function () {
                    if (dataSet.status.status.slice(-8) !== 'complete') {
                        $timeout.cancel(statusCheckPromise);
                        statusCheckPromise = $timeout($scope.statusCheck, 1000);
                    }
                });
            }
        });

        angular.forEach($scope.analyses, function (analysis) {
            if (analysis.status.slice(-8) !== 'complete') {
                Analyses.get(analysis.id).$promise.then(function (updatedAnalysis) {
                    angular.extend(analysis, updatedAnalysis);

                    if (analysis.status.slice(-8) !== 'complete') {
                        $timeout.cancel(statusCheckPromise);
                        statusCheckPromise = $timeout($scope.statusCheck, 1000);
                    }
                });
            }
        });
    };

    $scope.statusCheck();

    $scope.configureTimestamp = function ($index) {
        var promises = { timeZones: $http.get(settings.TIMEZONES_URL) };

        if (!$scope.dataFiles[$index].head) {
            promises.head = DataFiles.head($scope.dataFiles[$index].id);
        }

        $q.all(promises).then(function (responses) {
            if (responses.head) {
                if (responses.head.has_header) {
                    responses.head.header = responses.head.rows.shift();
                }

                $scope.dataFiles[$index].head = responses.head;
                $scope.dataFiles[$index].cols = [];
                angular.forEach($scope.dataFiles[$index].head.rows[0], function (v, k) {
                    $scope.dataFiles[$index].cols.push(k);
                });
            }

            $scope.timestampFile = $scope.dataFiles[$index];
            $scope.timeZones = responses.timeZones.data;

            Modals.openModal('configureTimestamp');
        });
    };

    $scope.upload = function (files) {
        var uploads = [];

        $scope.uploading = true;

        angular.forEach(files, function(file) {
            uploads.push($upload.upload({
                url: settings.API_URL + 'projects/' + project.id + '/add_file',
                file: file,
            }).then(function (response) {
                // Perform a 'get' so that the file object has $save and $delete methods
                DataFiles.get(response.data.id).then(function (getResponse) {
                    $scope.dataFiles.push(getResponse);
                    $scope.configureTimestamp($scope.dataFiles.length - 1);
                });
            }));
        });

        return $q.all(uploads).catch(function (rejection) {
                var error;

                if (rejection.data.file) {
                    error = rejection.data.file.join('\n');
                } else {
                    error = rejection.data;
                }

                alert(error);
            }).finally(function () {
                delete $scope.uploading;
                Modals.closeModal('uploadFile');
            });
    };

    $scope.errorsModal = {};

    $scope.showErrors = function (dataSet) {
        $scope.errorsModal.files = {};

        // Create hash of data map file names to data file names
        angular.forEach(dataSet.files, function (file) {
            angular.forEach($scope.dataFiles, function (dataFile) {
                if (dataFile.id === file.file) {
                    $scope.errorsModal.files[file.name] = dataFile.name;
                }
            });

            if (!$scope.errorsModal.files[file.name]) {
                $scope.errorsModal.files[file.name] = 'File "' + file.name + '"';
            }
        });

        $scope.errorsModal.errors = dataSet.errors;

        Modals.openModal('dataSetErrors');
    };

    $scope.rename = function (collectionName, index) {
        function getName(promptText) {
            if (!$scope[collectionName]) {
                throw 'Collection not found: ' + collectionName;
            }

            var originalName = $scope[collectionName][index].name,
                newName;

            promptText = promptText || '';

            if (promptText.length) {
                promptText += '\n\n';
            }

            promptText += 'Rename \'' + originalName + '\' to:';

            newName = prompt(promptText);

            if (newName === null) {
                return;
            }

            if (!newName.length) {
                getName('Name cannot be empty.');
            } else {
                $scope[collectionName][index].name = newName;
                $scope[collectionName][index].$save(function () {
                    if (collectionName === 'dataSets') {
                        $scope.statusCheck();
                    }
                }, function (rejection) {
                    $scope[collectionName][index].name = originalName;
                    getName(rejection.data.__all__.join('\n'));
                });
            }
        }

        getName();
    };

    $scope.delete = function (collectionName, index) {
        if (!$scope[collectionName]) {
            throw 'Collection not found: ' + collectionName;
        }

        if (!confirm('Delete \'' + $scope[collectionName][index].name + '\'?')) {
            return;
        }

        $scope[collectionName][index].$delete(function () {
            $scope[collectionName].splice(index, 1);

            if (collectionName === 'sharedAnalyses') {
                $scope.sharedAnalyses = SharedAnalyses.query(project.id);
            }
        });
    };

    $scope.viewAnalysis = function (analysis) {
        $scope.viewingAnalysis = analysis;
        delete $scope.viewingAnalysisData;
        Modals.openModal('viewAnalysis');

        Analyses.getData(analysis.id).then(function (outputData) {
            $scope.viewingAnalysisData = outputData;
        });
    };

    $scope.getAnalysisOutputUrl = function (analysisId) {
        return settings.API_URL + 'analyses/' + analysisId + '/download';
    };

    $scope.shareAnalysis = function (analysis) {
        SharedAnalyses.create(analysis.id).$promise.then(function (sharedAnalysis) {
            $scope.sharedAnalyses.push(sharedAnalysis);
            $scope.viewLink(analysis.id);
        });
    };

    $scope.viewLink = function (analysisId) {
        angular.forEach($scope.sharedAnalyses, function (sharedAnalysis) {
            if (sharedAnalysis.analysis === analysisId) {
                $scope.viewingLink = {
                    url: window.location.protocol + '//' + window.location.host + '/shared-analyses/' + analysisId + '/' + sharedAnalysis.key,
                    sharedAnalysis: sharedAnalysis,
                };
                Modals.openModal('viewLink');
            }
        });
    };

    $scope.revokeLink = function (analysisId) {
        if (confirm('Revoke sharing?')) {
            angular.forEach($scope.sharedAnalyses, function (sharedAnalysis) {
                if (sharedAnalysis.analysis === analysisId) {
                    sharedAnalysis.$delete(function () {
                        $scope.sharedAnalyses.splice($scope.sharedAnalyses.indexOf(sharedAnalysis), 1);
                    });
                }
            });
            Modals.closeModal('viewLink');
        }
    };
});
