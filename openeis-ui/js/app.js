angular.module('openeis-ui', [
    'openeis-ui.auth', 'openeis-ui.projects', 'openeis-ui.templates',
    'ngAnimate', 'ngRoute',
])
// URL of OpenEIS API, without trailing slash
.constant('API_URL', '/api')
// Route redirect for anonymous users (root-relative to HTML base)
.constant('ANON_HOME', '/')
// Route redirect for authenticated users (root-relative to HTML base)
.constant('AUTH_HOME', '/projects')
.config(function ($routeProvider, $locationProvider, $httpProvider) {
    $routeProvider
        .otherwise({
            templateUrl: 'partials/404.html',
        });

    $locationProvider.html5Mode(true);

    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
})
.run(function (Auth) {
    Auth.relocate();
});
