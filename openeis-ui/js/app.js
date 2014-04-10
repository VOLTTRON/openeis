angular.module('openeis-ui', [
    'openeis-ui.auth', 'openeis-ui.projects',
    'ngAnimate', 'ngCookies', 'ngRoute',
])
.constant('API_URL', '/api') // URL of OpenEIS API, without trailing slash
.config(function ($routeProvider, $locationProvider, $httpProvider) {
    $routeProvider
        .otherwise({
            templateUrl: '/partials/404.html',
        });

    $locationProvider.html5Mode(true);

    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
})
.run(function ($rootScope, Auth, $location) {
    $rootScope.$on('$routeChangeError', function (event, current, previous, rejection) {
        console.log(rejection);
        if (rejection.status === 401) {
            $location.url('/');
        }
    });
})
