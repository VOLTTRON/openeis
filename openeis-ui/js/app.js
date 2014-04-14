angular.module('openeis-ui', [
    'openeis-ui.auth', 'openeis-ui.projects',
    'ngAnimate', 'ngRoute',
])
.constant('API_URL', '/api') // URL of OpenEIS API, without trailing slash
.constant('ANON_HOME', '/')
.constant('AUTH_HOME', '/projects')
.config(function ($routeProvider, $locationProvider, $httpProvider) {
    $routeProvider
        .otherwise({
            templateUrl: '/partials/404.html',
        });

    $locationProvider.html5Mode(true);

    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
})
