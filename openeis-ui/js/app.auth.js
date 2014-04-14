angular.module('openeis-ui.auth', ['ngResource', 'ngRoute'])
.config(function ($routeProvider) {
    $routeProvider
        .when('/', {
            controller: 'LoginCtrl',
            templateUrl: '/partials/login.html',
        });
})
.factory('Auth', function ($resource, API_URL, $q) {
    var Auth = this;

    Auth.authenticated = null;
    Auth.resource = $resource(API_URL + '/auth');

    Auth.isAuthenticated = function () {
        var deferred = $q.defer();

        if (Auth.authenticated === null) {
            Auth.resource.get().$promise.then(function () {
                Auth.authenticated = true;
                deferred.resolve();
            }, function (response) {
                Auth.authenticated = false;
                deferred.reject(response);
            });
        } else if (Auth.authenticated === false) {
            deferred.reject({ status: 403 });
        } else if (Auth.authenticated === true) {
            deferred.resolve();
        }

        return deferred.promise;
    };

    Auth.logIn = function(credentials) {
        var deferred = $q.defer();

        Auth.resource.save(credentials).$promise.then(function () {
            Auth.authenticated = true;
            deferred.resolve();
        }, function (response) {
            deferred.reject(response);
        });

        return deferred.promise;
    };

    Auth.logOut = function(credentials) {
        var deferred = $q.defer();

        Auth.resource.delete().$promise.then(function () {
            Auth.authenticated = false;
            deferred.resolve();
        }, function (response) {
            deferred.reject(response);
        });

        return deferred.promise;
    };

    return Auth;
})
.controller('LoginCtrl', function ($scope, $location, Auth, AUTH_HOME) {
    $scope.form = {};
    $scope.form.logIn = function () {
        Auth.logIn({
            username: $scope.form.username,
            password: $scope.form.password,
        }).then(function () {
            $location.url(AUTH_HOME);
        }, function (response) {
            switch (response.status) {
                case 403:
                $scope.form.error = 'Authentication failed.';
                break;

                default:
                $scope.form.error = 'Unknown error occurred.';
            }
        });
    };
})
.controller('TopBarCtrl', function ($scope, Auth, $location, ANON_HOME) {
    $scope.logOut = function () {
        Auth.logOut().then(function () {
            $location.url(ANON_HOME);
        });
    };
})
.run(function (Auth, ANON_HOME, AUTH_HOME, $location) {
    Auth.isAuthenticated().then(function () {
        if ($location.path() === '/') {
            $location.url(AUTH_HOME);
        }
    }, function () {
        if ($location.path() !== '/') {
            $location.url(ANON_HOME);
        }
    });
});
