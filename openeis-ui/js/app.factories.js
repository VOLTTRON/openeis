angular.module('openeis-ui.factories', ['ngResource'])
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
            deferred.reject({ status: 401 });
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
