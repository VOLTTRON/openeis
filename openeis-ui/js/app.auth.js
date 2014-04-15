angular.module('openeis-ui.auth', ['ngResource', 'ngRoute'])
.config(function ($routeProvider) {
    $routeProvider
        .when('/', {
            controller: 'LoginCtrl',
            templateUrl: '/partials/login.html',
        });
})
.factory('Auth', function ($resource, API_URL, $q) {
    var authenticated = null,
        username = 'Anonymous',
        resource = $resource(API_URL + '/auth');

    this.username = function () {
        return username;
    };

    this.isAuthenticated = function () {
        var deferred = $q.defer();

        if (authenticated === null) {
            resource.get().$promise.then(function (response) {
                authenticated = true;
                username = response.username;
                deferred.resolve();
            }, function (rejection) {
                authenticated = false;
                deferred.reject(rejection);
            });
        } else if (authenticated === false) {
            deferred.reject({ status: 403 });
        } else if (authenticated === true) {
            deferred.resolve();
        }

        return deferred.promise;
    };

    this.logIn = function(credentials) {
        var deferred = $q.defer();

        resource.save(credentials).$promise.then(function (response) {
            authenticated = true;
            username = response.username;
            deferred.resolve();
        }, function (rejection) {
            deferred.reject(rejection);
        });

        return deferred.promise;
    };

    this.logOut = function(credentials) {
        var deferred = $q.defer();

        resource.delete().$promise.then(function () {
            authenticated = false;
            username = 'Anonymous';
            deferred.resolve();
        }, function (rejection) {
            deferred.reject(rejection);
        });

        return deferred.promise;
    };

    return this;
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
    $scope.username = Auth.username();

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
