angular.module('openeis-ui.projects', ['openeis-ui.auth', 'ngResource', 'ngRoute'])
.config(function ($routeProvider) {
    // Add method for routes requiring authentication
    $routeProvider.whenAuthenticated = function(path, route) {
        route.resolve = route.resolve || {};

        angular.extend(route.resolve, {
            // Use array syntax until ngmin can do it for us
            authenticated: ['Auth', function (Auth) {
                return Auth.isAuthenticated();
            }]
        });

        return $routeProvider.when(path, route);
    };

    $routeProvider
        .whenAuthenticated('/projects', {
            controller: 'ProjectsCtrl',
            templateUrl: '/partials/projects.html',
            resolve: {
                projects: ['Projects', function(Projects) {
                    return Projects.query();
                }]
            },
        })
        .whenAuthenticated('/projects/:projectId', {
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
.controller('ProjectCtrl', function ($scope, project) {
    $scope.project = project;
})
