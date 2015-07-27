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
.controller('ConfigureTimestampCtrl', function ($scope, DataFiles, $http, Modals) {
    $scope.modal = {
        columns: {},
        timeOffset: $scope.timestampFile.time_offset || 0,
        timeZone: $scope.timestampFile.time_zone || jstz.determine().name(),
    };

    if ($scope.timestampFile.timestamp && $scope.timestampFile.timestamp.columns) {
        angular.forEach($scope.timestampFile.timestamp.columns, function (column) {
            $scope.modal.columns[column] = true;
        });
    }

    $scope.preview = function () {
        $scope.selectedColumns = [];

        angular.forEach($scope.modal.columns, function (selected, column) {
            if (selected === true) {
                $scope.selectedColumns.push(parseInt(column));
            }
        });

        if (!$scope.selectedColumns.length) {
            alert('Please select at least one column.');
            return;
        }

        DataFiles.timestamps(
            $scope.timestampFile.id,
            $scope.modal.timeOffset,
            $scope.modal.timeZone,
            $scope.selectedColumns.join(',')
        ).then(function (response) {
            $scope.modal.confirm = true;
            $scope.modal.timestamps = response;
        }, function (rejection) {
            alert(angular.toJson(rejection.data));
        });
    };

    $scope.save = function () {
        var timestamp = { columns: $scope.selectedColumns };

        DataFiles.update({
            id: $scope.timestampFile.id,
            timestamp: timestamp,
            time_offset: $scope.modal.timeOffset,
            time_zone: $scope.modal.timeZone,
        }).then(function (file) {
            $scope.timestampFile.timestamp = timestamp;
            $scope.timestampFile.time_zone = $scope.modal.timeZone;
            Modals.closeModal('configureTimestamp');
        }, function (rejection) {
            alert(angular.toJson(rejection));
        });
    };
});
