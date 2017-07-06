// Copyright (c) 2014, Battelle Memorial Institute
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
// ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
// The views and conclusions contained in the software and documentation are those
// of the authors and should not be interpreted as representing official policies,
// either expressed or implied, of the FreeBSD Project.
//
//
// This material was prepared as an account of work sponsored by an
// agency of the United States Government.  Neither the United States
// Government nor the United States Department of Energy, nor Battelle,
// nor any of their employees, nor any jurisdiction or organization
// that has cooperated in the development of these materials, makes
// any warranty, express or implied, or assumes any legal liability
// or responsibility for the accuracy, completeness, or usefulness or
// any information, apparatus, product, software, or process disclosed,
// or represents that its use would not infringe privately owned rights.
//
// Reference herein to any specific commercial product, process, or
// service by trade name, trademark, manufacturer, or otherwise does
// not necessarily constitute or imply its endorsement, recommendation,
// or favoring by the United States Government or any agency thereof,
// or Battelle Memorial Institute. The views and opinions of authors
// expressed herein do not necessarily state or reflect those of the
// United States Government or any agency thereof.
//
// PACIFIC NORTHWEST NATIONAL LABORATORY
// operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
// under Contract DE-AC05-76RL01830

angular.module('openeis-ui.services.auth', ['ngResource', 'ngRoute'])
.provider('authRoute', function ($routeProvider) {
    // Wrapper around $routeProvider to add check for auth status

    this.whenAnon = function (path, route) {
        route.resolve = route.resolve || {};
        angular.extend(route.resolve, { anon: ['authRoute', function(authRoute) { return authRoute.requireAnon(); }] });
        $routeProvider.when(path, route);
        return this;
    };

    this.whenAuth = function (path, route) {
        route.resolve = route.resolve || {};
        angular.extend(route.resolve, { auth: ['authRoute', function(authRoute) { return authRoute.requireAuth(); }] });
        $routeProvider.when(path, route);
        return this;
    };

    this.when = function (path, route) {
        $routeProvider.when(path, route);
        return this;
    };

    this.$get = function (Auth, $q, $location) {
        return {
            requireAnon: function () {
                var deferred = $q.defer();

                Auth.account().then(function (account) {
                    if (account) {
                        $location.url(settings.AUTH_HOME);
                        deferred.reject();
                    } else {
                        deferred.resolve();
                    }
                });

                return deferred.promise;
            },
            requireAuth: function () {
                var deferred = $q.defer();

                Auth.account().then(function (account) {
                    if (account) {
                        deferred.resolve();
                    } else {
                        Auth.loginRedirect($location.url());
                        $location.url(settings.LOGIN_PAGE);
                        deferred.reject();
                    }
                });

                return deferred.promise;
            },
        };
    };
})
.service('Auth', function ($resource, $q, $location, $rootScope) {
    var Auth = this,
        account = null,
        resource = $resource(settings.API_URL + 'account', null, {
            create: { method: 'POST' },
            update: { method: 'PATCH' },
        }),
        loginResource = $resource(settings.API_URL + 'account/login'),
        pwChangeResource = $resource(settings.API_URL + 'account/change_password'),
        pwResetResource = $resource(settings.API_URL + 'account/password_reset', null, {
            put: { method: 'PUT' },
        }),
        loginRedirect = null;

    function updateAccount() {
        var deferred = $q.defer();

        resource.get().$promise
            .then(function (response) {
                account = response;
            }, function () {
                account = false;
            })
            .finally(function () {
                $rootScope.$broadcast('accountChange');
                deferred.resolve(account);
            });

        return deferred.promise;
    }

    Auth.account = function () {
        if (account === null) {
            return updateAccount();
        }

        var deferred = $q.defer();
        deferred.resolve(account);
        return deferred.promise;
    };

    Auth.accountCreate = function (account) {
        return resource.create(account).$promise;
    };

    Auth.accountUpdate = function (account) {
        return resource.update(account).$promise;
    };

    Auth.accountPassword = function (password) {
        return pwChangeResource.save(password).$promise;
    };

    Auth.accountRecover1 = function (id) {
        return pwResetResource.save({ username_or_email: id }).$promise;
    };

    Auth.accountRecover2 = function (params) {
        return pwResetResource.put(params).$promise;
    };

    Auth.logIn = function (credentials) {
        var deferred = $q.defer();

        loginResource.save(credentials, function () {
            updateAccount().then(function () {
                if (loginRedirect !== null) {
                    $location.url(loginRedirect);
                    loginRedirect = null;
                } else {
                    $location.url(settings.AUTH_HOME);
                }
                deferred.resolve();
            });
        }, function (rejection) {
            deferred.reject(rejection);
        });

        return deferred.promise;
    };

    Auth.loginRedirect = function (url) {
        loginRedirect = url;
    };

    Auth.logOut = function () {
        var deferred = $q.defer();

        loginResource.delete(function () {
            account = false;
            $rootScope.$broadcast('accountChange');
            $location.url(settings.LOGIN_PAGE);
            deferred.resolve();
        }, function (rejection) {
            deferred.reject(rejection);
        });

        return deferred.promise;
    };
});
