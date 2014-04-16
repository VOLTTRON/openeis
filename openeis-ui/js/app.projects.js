angular.module('openeis-ui.projects', [
    'openeis-ui.auth', 'openeis-ui.file',
    'ngResource', 'ngRoute', 'mm.foundation', 'angularFileUpload',
])
.config(function ($routeProvider) {
    $routeProvider
        .when('/projects', {
            controller: 'ProjectsCtrl',
            templateUrl: 'partials/projects.html',
            resolve: {
                projects: ['Projects', function(Projects) {
                    return Projects.query();
                }]
            },
        })
        .when('/projects/:projectId', {
            controller: 'ProjectCtrl',
            templateUrl: 'partials/project.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                projectFiles: ['ProjectFiles', '$route', function(ProjectFiles, $route) {
                    return ProjectFiles.query($route.current.params.projectId);
                }],
            },
        });
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
        resource: $resource(API_URL + '/files/:fileId'),
        query: function (projectId) {
            return ProjectFiles.resource.query({ project: projectId }).$promise;
        },
        delete: function (fileId) {
            return ProjectFiles.resource.delete({ fileId: fileId }).$promise;
        },
    };

    return ProjectFiles;
})
.controller('ProjectsCtrl', function ($scope, projects) {
    $scope.projects = projects;
})
.controller('ProjectCtrl', function ($scope, project, projectFiles, $modal, $upload, API_URL, ProjectFiles) {
    $scope.project = project;
    $scope.projectFiles = projectFiles;

    $scope.upload = function (fileInput) {
        angular.forEach(fileInput[0].files, function(file) {
            $upload.upload({
                url: API_URL + '/projects/' + project.id + '/add_file',
                file: file,
            }).then(function (response) {
                // Inject mock file contents for now. Remove once
                // API returns it or provides a method for retrieval
                response.data.top = [
                    'These lines were manually injected',
                    'into the API\'s response. The first',
                    'few lines of the file will be displayed',
                    'once the API actually returns them.',
                ].join('\n');

               $scope.projectFiles.push(response.data);
               $scope.openModal(response.data);
               fileInput.val('');
            });
        });
    };

    $scope.deleteFile = function ($index) {
        ProjectFiles.delete($scope.projectFiles[$index].id).then(function (response) {
            $scope.projectFiles.splice($index, 1);
        });
    };

    $scope.hasFiles = function () {
        return $scope.projectFiles.length;
    };

    $scope.openModal = function (file) {
        var modalInstance = $modal.open({
            templateUrl: 'partials/addfile.html',
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
});
