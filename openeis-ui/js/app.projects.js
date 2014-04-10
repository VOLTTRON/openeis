angular.module('openeis-ui.projects', [
    'openeis-ui.auth', 'ngResource', 'ngRoute', 'mm.foundation',
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
                }]
            },
        })
})
.factory('Projects', function ($resource, API_URL) {
    var Projects = {
        resource: $resource(API_URL + '/projects/:projectId', { projectId: '@id' }),
        get: function (projectId) {
            return Projects.resource.get({ projectId: projectId}).$promise;
        },
        query: function (projectId) {
            return Projects.resource.query().$promise;
        },
    };

    return Projects;
})
.controller('ProjectsCtrl', function ($scope, projects) {
    $scope.projects = projects;
})
.controller('ProjectCtrl', function ($scope, project, $modal) {
    $scope.project = project;

    $scope.open = function () {
        var modalInstance = $modal.open({
            templateUrl: '/partials/addfile.html',
            controller: 'AddFileCtrl',
        });

        modalInstance.result.then(function (response) {
            console.log(response);
        }, function (rejection) {
            console.log(rejection);
        });
    };
})
.controller('AddFileCtrl', function ($scope, $modalInstance) {
    $scope.ok = function () {
        $modalInstance.close("Clicked OK.");
    };

    $scope.cancel = function () {
        $modalInstance.dismiss("Cancelled.");
    };
})
