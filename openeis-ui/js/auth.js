angular.module('openeis-ui.auth', ['ngResource', 'ngRoute'])
.provider('authRoute', function ($routeProvider) {
    // Wrapper around $routeProvider to add check for auth status

    this.whenAnon = function (path, route) {
        route.resolve = route.resolve || {};
        angular.extend(route.resolve, { anon: ['Auth', function(Auth) { return Auth.requireAnon(); }] });
        $routeProvider.when(path, route);
        return this;
    };

    this.whenAuth = function (path, route) {
        route.resolve = route.resolve || {};
        angular.extend(route.resolve, { auth: ['Auth', function(Auth) { return Auth.requireAuth(); }] });
        $routeProvider.when(path, route);
        return this;
    };

    this.$get = $routeProvider.$get;
})
.config(function (authRouteProvider) {
    authRouteProvider
        .whenAnon('/', {
            controller: 'LoginCtrl',
            templateUrl: 'partials/login.html',
        })
        .whenAnon('/sign-up', {
            controller: 'SignUpCtrl',
            templateUrl: 'partials/signup.html',
        })
        .whenAuth('/account', {
            controller: 'AccountCtrl',
            templateUrl: 'partials/account.html',
        });
})
.service('Auth', function ($resource, API_URL, $q, ANON_HOME, AUTH_HOME, $location) {
    var authenticated = null,
        username = 'Anonymous',
        resource = $resource(API_URL + '/auth');

    this.username = function () {
        return username;
    };

    this.init = function () {
        var deferred = $q.defer();

        resource.get(function (response) {
            authenticated = true;
            username = response.username;
            deferred.resolve();
        }, function () {
            authenticated = false;
            deferred.resolve();
        });

        return deferred.promise;
    };

    this.logIn = function(credentials) {
        var deferred = $q.defer();

        resource.save(credentials, function (response) {
            authenticated = true;
            username = response.username;
            deferred.resolve();
        }, function (rejection) {
            deferred.reject(rejection);
        });

        return deferred.promise;
    };

    this.logOut = function() {
        var deferred = $q.defer();

        resource.delete(function () {
            authenticated = false;
            username = 'Anonymous';
            deferred.resolve();
        }, function (rejection) {
            deferred.reject(rejection);
        });

        return deferred.promise;
    };

    this.requireAnon = function () {
        var deferred = $q.defer();

        function check() {
            if (authenticated) {
                $location.url(AUTH_HOME);
                deferred.reject();
            } else {
                deferred.resolve();
            }
        }

        if (authenticated === null) {
            this.init().then(function () {
                check();
            });
        } else {
            check();
        }

        return deferred.promise;
    };

    this.requireAuth = function () {
        var deferred = $q.defer();

        function check() {
            if (!authenticated) {
                $location.url(ANON_HOME);
                deferred.reject();
            } else {
                deferred.resolve();
            }
        }

        if (authenticated === null) {
            this.init().then(function () {
                check();
            });
        } else {
            check();
        }

        return deferred.promise;
    };
})
.controller('LoginCtrl', function ($scope, $location, Auth, AUTH_HOME) {
    $scope.logIn = function () {
        Auth.logIn({
            username: $scope.form.username,
            password: $scope.form.password,
        }).then(function () {
            $location.url(AUTH_HOME);
        }, function (response) {
            $scope.form.error = response.status;
        });
    };
    $scope.clearError = function () {
        $scope.form.error = null;
    };
})
.controller('SignUpCtrl', function ($scope, $location, Auth, AUTH_HOME) {
    $scope.form = {};
    $scope.signUp = function () {
        console.log($scope.form);
    };
})
.controller('AccountCtrl', function ($scope, Auth) {
    $scope.form = {
        changed: false,
        submit: function () {
            console.log($scope.account);
        },
    };

    $scope.account = {
        username: Auth.username(),
        email: Auth.username() +'.email@example.com',
    };

    $scope.$watchCollection('account', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.form.changed = true;
        }
    });
})
.controller('TopBarCtrl', function ($scope, Auth, $location, ANON_HOME) {
    $scope.username = Auth.username();

    $scope.logOut = function () {
        Auth.logOut().then(function () {
            $location.url(ANON_HOME);
        });
    };
});
