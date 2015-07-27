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

var base = document.getElementsByTagName('base')[0];
if (base) { base.setAttribute('href', settings.BASE_HREF); }

angular.module('openeis-ui', [
    'angularFileUpload',
    'ngAnimate',
    'ngResource',
    'ngRoute',
    'ngSanitize',
    'openeis-ui.components.modals',
    'openeis-ui.directives.analysis-report',
    'openeis-ui.directives.file-upload',
    'openeis-ui.directives.sensor-container',
    'openeis-ui.filters',
    'openeis-ui.services.analyses',
    'openeis-ui.services.applications',
    'openeis-ui.services.auth',
    'openeis-ui.services.data-files',
    'openeis-ui.services.data-maps',
    'openeis-ui.services.data-set-filters',
    'openeis-ui.services.data-sets',
    'openeis-ui.services.projects',
    'openeis-ui.services.shared-analyses',
])
.config(function ($routeProvider, $locationProvider, $httpProvider, authRouteProvider) {
    $routeProvider
        .otherwise({
            templateUrl: '404.tpl.html',
        });

    $locationProvider.html5Mode(true);

    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';

    authRouteProvider
        .whenAnon('/', {
            controller: 'LoginCtrl',
            templateUrl: 'login.tpl.html',
        })
        .whenAnon('/recovery', {
            controller: 'RecoveryCtrl',
            templateUrl: 'recovery.tpl.html',
        })
        .whenAnon('/sign-up', {
            controller: 'SignUpCtrl',
            templateUrl: 'signup.tpl.html',
        })
        .whenAuth('/account', {
            controller: 'AccountCtrl',
            templateUrl: 'account.tpl.html',
        })
        .whenAuth('/projects', {
            controller: 'ProjectsCtrl',
            templateUrl: 'projects.tpl.html',
            resolve: {
                projects: ['Projects', function(Projects) {
                    return Projects.query();
                }]
            },
        })
        .whenAuth('/projects/:projectId', {
            controller: 'ProjectCtrl',
            templateUrl: 'project.tpl.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                dataFiles: ['DataFiles', '$route', function(DataFiles, $route) {
                    return DataFiles.query($route.current.params.projectId);
                }],
                dataSets: ['DataSets', '$route', function(DataSets, $route) {
                    return DataSets.query($route.current.params.projectId).$promise;
                }],
                dataMaps: ['DataMaps', '$route', function(DataMaps, $route) {
                    return DataMaps.query($route.current.params.projectId).$promise;
                }],
                analyses: ['Analyses', '$route', function(Analyses, $route) {
                    return Analyses.query($route.current.params.projectId).$promise;
                }],
                sharedAnalyses: ['SharedAnalyses', '$route', function(SharedAnalyses, $route) {
                    return SharedAnalyses.query($route.current.params.projectId).$promise;
                }],
            },
        })
        .whenAuth('/projects/:projectId/new-data-map', {
            controller: 'NewDataMapCtrl',
            templateUrl: 'new-data-map.tpl.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                dataFiles: ['DataFiles', '$route', function(DataFiles, $route) {
                    return DataFiles.query($route.current.params.projectId);
                }],
                newDataMap: ['$route', 'DataMaps', function ($route, DataMaps) {
                    return DataMaps.getDefaultMap($route.current.params.projectId);
                }],
            },
        })
        .whenAuth('/projects/:projectId/new-data-set', {
            controller: 'NewDataSetCtrl',
            templateUrl: 'new-data-set.tpl.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                dataFiles: ['DataFiles', '$route', function(DataFiles, $route) {
                    return DataFiles.query($route.current.params.projectId);
                }],
                dataMaps: ['DataMaps', '$route', function(DataMaps, $route) {
                    return DataMaps.query($route.current.params.projectId);
                }],
            },
        })
        .whenAuth('/projects/:projectId/datamaps/:dataMapId', {
            controller: 'DataMapCtrl',
            templateUrl: 'data-map.tpl.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                dataMap: ['DataMaps', '$route', function(DataMaps, $route) {
                    return DataMaps.get($route.current.params.dataMapId).$promise;
                }],
            },
        })
        .whenAuth('/projects/:projectId/datamaps/:dataMapId/clone-and-edit', {
            controller: 'NewDataMapCtrl',
            templateUrl: 'new-data-map.tpl.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                dataFiles: ['DataFiles', '$route', function(DataFiles, $route) {
                    return DataFiles.query($route.current.params.projectId);
                }],
                newDataMap: ['$q', '$route', 'DataFiles', 'DataMaps', function ($q, $route, DataFiles, DataMaps) {
                    return $q.all({
                        dataMap: DataMaps.get($route.current.params.dataMapId).$promise,
                        dataFiles: DataFiles.query($route.current.params.projectId),
                    }).then(function (responses) {
                        return DataMaps.ensureFileMetaData(responses.dataFiles).then(function () {
                            return DataMaps.unFlattenMap(responses.dataMap, responses.dataFiles);
                        });
                    });
                }],
            },
        })
        .whenAuth('/projects/:projectId/datasets/:dataSetId', {
            controller: 'DataSetCtrl',
            templateUrl: 'data-set.tpl.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                dataSet: ['DataSets', '$route', function(DataSets, $route) {
                    return DataSets.get($route.current.params.dataSetId).$promise;
                }],
                head: ['DataSets', '$route', function(DataSets, $route) {
                    return DataSets.head($route.current.params.dataSetId).$promise;
                }],
            },
        })
        .whenAuth('/projects/:projectId/datasets/:dataSetId/manipulate', {
            controller: 'DataSetManipulateCtrl',
            templateUrl: 'data-set-manipulate.tpl.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                dataSet: ['DataSets', '$route', function(DataSets, $route) {
                    return DataSets.get($route.current.params.dataSetId).$promise;
                }],
            },
        })
        .when('/shared-analyses/:analysisId/:key', {
            controller: 'SharedAnalysesCtrl',
            templateUrl: 'shared-analyses.tpl.html',
        });
})
.controller('AppCtrl', function ($http, $scope, Modals, Auth) {
    $scope.modalOpen = Modals.modalOpen;

    $scope.$on('accountChange', function () {
        Auth.account().then(function (account) {
            $scope.account = account;
        });
    });

    $scope.logOut = function () {
        Auth.logOut();
    };

    $http.get(settings.API_URL + 'version').success(function (version) {
        $scope.version = [
            'v',
            version.version,
            ' (',
            version.revision,
            '#',
            version.vcs_version,
            ') ',
            version.updated,
        ].join('');
    });
})
.run(function ($rootScope, $rootElement) {
    $rootScope.$on('$viewContentLoaded', function () {
        window.setTimeout(function() {
            $rootElement.find('input').checkAndTriggerAutoFillEvent();
        }, 200);
    });
});
