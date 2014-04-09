angular.module('openeis.ui', ['ngAnimate', 'ngCookies', 'ngResource', 'ngRoute', 'djangoRESTResources'])
.constant('API_URL', '/api') // URL of OpenEIS API, without trailing slash
.config(function ($routeProvider, $locationProvider, $httpProvider) {
    $routeProvider
    .when('/', {
        controller: 'LoginCtrl',
        templateUrl: '/partials/login.html',
    })
    .when('/projects', {
        controller: 'ProjectsCtrl',
        templateUrl: '/partials/projects.html',
    })
    .when('/projects/:projectId', {
        controller: 'ProjectCtrl',
        template: '<h2 ng-if="project">{{project.name}} (id: {{project.id}})</h2>',
    })
    .otherwise({
        templateUrl: '/partials/404.html',
    });

    $locationProvider.html5Mode(true);

    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
})
.factory('Auth', function ($resource, $location, API_URL) {
    return $resource(API_URL + '/auth', null, {
        check: { method: 'GET' },
        logIn: { method: 'POST', interceptor: {
            response: function () { $location.url('/projects'); },
        }},
        logOut: { method: 'DELETE', interceptor: {
            response: function () { $location.url('/'); },
        }},
    });
})
.factory('Projects', function (djResource, API_URL) {
    return djResource(API_URL + '/projects/:projectId/', { projectId: '@id' });
})
.controller('LoginCtrl', function ($scope, $location, Auth, $cookies) {
    Auth.check(
        function () { $location.url('/projects'); },
        function () { $scope.anonymous = true; }
    );

    $scope.form = {};
    $scope.form.logIn = function () {
        Auth.logIn(
            null,
            { username: $scope.form.username, password: $scope.form.password },
            null,
            function (response) {
                switch (response.status) {
                    case 401:
                    $scope.form.error = 'Authentication failed.'
                    break;

                    case 405:
                    $location.url('/projects');
                    break;

                    default:
                    $scope.form.error = 'Unknown error occurred.'
                }
            }
        );
    };
})
.controller('ProjectsCtrl', function ($scope, Projects, Auth) {
    Projects.query(function (results) {
        $scope.projects = results;
    });

    $scope.logOut = function () {
        Auth.logOut();
    };
})
.controller('ProjectCtrl', function ($scope, $routeParams, Projects) {
    Projects.get({ projectId: $routeParams.projectId }, function (result) {
        $scope.project = result;
    });
});
