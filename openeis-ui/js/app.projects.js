angular.module('openeis-ui.projects', [
    'openeis-ui.auth', 'ngResource', 'ngRoute', 'mm.foundation', 'angularFileUpload',
])
.config(function ($routeProvider) {
    $routeProvider
        .when('/projects', {
            controller: 'ProjectsCtrl',
            templateUrl: '/partials/projects.html',
            resolve: {
                projects: ['Projects', function(Projects) {
                    return Projects.query();
                }]
            },
        })
        .when('/projects/:projectId', {
            controller: 'ProjectCtrl',
            templateUrl: '/partials/project.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                projectFiles: ['ProjectFiles', '$route', function(ProjectFiles, $route) {
                    return ProjectFiles.query($route.current.params.projectId);
                }],
            },
        })
})
.factory('Projects', function ($resource, API_URL) {
    var Projects = {
        resource: $resource(API_URL + '/projects/:projectId', { projectId: '@id' }),
        get: function (projectId) {
            return Projects.resource.get({ projectId: projectId}).$promise;
        },
        query: function () {
            return Projects.resource.query().$promise;
        },
    };

    return Projects;
})
.factory('ProjectFiles', function ($resource, API_URL) {
    var ProjectFiles = {
        resource: $resource(API_URL + '/files?project=:projectId'),
        query: function (projectId) {
            return ProjectFiles.resource.query({ projectId: projectId }).$promise;
        },
    };

    return ProjectFiles;
})
.controller('ProjectsCtrl', function ($scope, projects) {
    $scope.projects = projects;
})
.controller('ProjectCtrl', function ($scope, project, projectFiles, $modal, $upload, API_URL) {
    $scope.project = project;
    $scope.projectFiles = projectFiles;

    $scope.onFileSelect = function($files) {
        //$files: an array of files selected, each file has name, size, and type.
        for (var i = 0; i < $files.length; i++) {
            var file = $files[i];

            $scope.uploading = true;

            $scope.upload = $upload.upload({
                url: API_URL + '/projects/' + project.id + '/add_file',
                method: 'POST',
                file: file, // or list of files: $files for html5 only
            }).progress(function(evt) {
                console.log('percent: ' + parseInt(100.0 * evt.loaded / evt.total));
            }).success(function(data, status, headers, config) {
                $scope.uploading = false;

                // Inject mock file contents unfil API returns it,
                // or provides method for retrieval
                data.top = [
                    'These lines were manually injected',
                    'into the API\'s response. The first',
                    'few lines of the file will be displayed',
                    'once the API actually returns them.',
                ].join('\n');

                $scope.projectFiles.push(data);
                $scope.openModal(data);
            }).error(function () {
                $scope.uploading = false;
            })
            //.then(success, error, progress);
        }
    };

    $scope.openModal = function (file) {
        var modalInstance = $modal.open({
            templateUrl: '/partials/addfile.html',
            controller: 'FileModalCtrl',
            resolve: {
                file: function () {
                    return file;
                },
            },
        });

        modalInstance.result.then(function (response) {
            console.log(response);
        }, function (rejection) {
            console.log(rejection);
        });
    };
})
.controller('FileModalCtrl', function ($scope, $modalInstance, file) {
    $scope.file = file;

    $scope.ok = function () {
        $modalInstance.close("Clicked OK.");
    };

    $scope.cancel = function () {
        $modalInstance.dismiss("Cancelled.");
    };
})
