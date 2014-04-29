describe('openeis-ui.auth', function () {
    var LOGIN_PAGE = '/path/to/login/page',
        AUTH_HOME = '/path/to/auth/home';

    beforeEach(function () {
        module('openeis-ui.auth');

        module(function($provide) {
            $provide.constant('API_URL', '/api');
            $provide.constant('LOGIN_PAGE', LOGIN_PAGE);
            $provide.constant('AUTH_HOME', AUTH_HOME);
        });
    });

    describe('authRoute provider', function () {
        var authRouteProvider;

        beforeEach(module(function ($provide, _authRouteProvider_) {
            $provide.value('Auth', {
                requireAnon: function () {},
                requireAuth: function () {},
            });

            authRouteProvider = _authRouteProvider_;
        }));

        describe('whenAnon method', function () {
            it('should add an anon resolve', function () {
                inject(function (authRoute) {
                    expect(authRoute.routes['/anon-test']).not.toBeDefined();

                    authRouteProvider.whenAnon('/anon-test', {});

                    expect(authRoute.routes['/anon-test'].resolve.anon).toBeDefined();
                });
            });

            it('should be chainable', function () {
                inject(function (authRoute) {
                    expect(authRoute.routes['/anon-test']).not.toBeDefined();
                    expect(authRoute.routes['/anon-test-2']).not.toBeDefined();
                    expect(authRoute.routes['/auth-test']).not.toBeDefined();

                    authRouteProvider
                        .whenAnon('/anon-test', {})
                        .whenAnon('/anon-test-2', {})
                        .whenAuth('/auth-test', {});

                    expect(authRoute.routes['/anon-test']).toBeDefined();
                    expect(authRoute.routes['/anon-test-2']).toBeDefined();
                    expect(authRoute.routes['/auth-test']).toBeDefined();
                });
            });
        });

         describe('whenAuth method', function () {
            it('should add an auth resolve', function () {
                inject(function (authRoute) {
                    expect(authRoute.routes['/auth-test']).not.toBeDefined();

                    authRouteProvider.whenAuth('/auth-test', {});

                    expect(authRoute.routes['/auth-test'].resolve.auth).toBeDefined();
                });
            });

            it('should be chainable', function () {
                inject(function (authRoute) {
                    expect(authRoute.routes['/auth-test']).not.toBeDefined();
                    expect(authRoute.routes['/auth-test-2']).not.toBeDefined();
                    expect(authRoute.routes['/anon-test']).not.toBeDefined();

                    authRouteProvider
                        .whenAuth('/auth-test', {})
                        .whenAuth('/auth-test-2', {})
                        .whenAnon('/anon-test', {});

                    expect(authRoute.routes['/auth-test']).toBeDefined();
                    expect(authRoute.routes['/auth-test-2']).toBeDefined();
                    expect(authRoute.routes['/anon-test']).toBeDefined();
                });
            });
        });
    });

    describe('Auth service', function () {
        var Auth, $httpBackend;

        beforeEach(function () {
            inject(function (_Auth_, _$httpBackend_) {
                Auth = _Auth_;
                $httpBackend = _$httpBackend_;
            });
        });

        afterEach(function () {
            $httpBackend.verifyNoOutstandingExpectation();
        });

        describe('init method', function () {
            it('should update the username property', function () {
                $httpBackend.expectGET('/api/auth').respond('{"username":"TestUser"}');
                Auth.init();

                expect(Auth.username()).toEqual('Anonymous');
                $httpBackend.flush();
                expect(Auth.username()).toEqual('TestUser');
            });
        });

        describe('logIn and logOut methods', function () {
            it('should update the username property if successful', function () {
                $httpBackend.expectPOST('/api/auth').respond('{"username":"TestUser"}');
                Auth.logIn({ username: 'TestUser', password: 'testpassword' });

                expect(Auth.username()).toEqual('Anonymous');
                $httpBackend.flush();
                expect(Auth.username()).toEqual('TestUser');

                $httpBackend.expectDELETE('/api/auth').respond(204, '');
                Auth.logOut();

                expect(Auth.username()).toEqual('TestUser');
                $httpBackend.flush();
                expect(Auth.username()).toEqual('Anonymous');
            });

            it('should not update the username property if unsuccessful', function () {
                $httpBackend.expectPOST('/api/auth').respond(403, '');
                Auth.logIn({ username: 'TestUser', password: 'testpassword' });

                expect(Auth.username()).toEqual('Anonymous');
                $httpBackend.flush();
                expect(Auth.username()).toEqual('Anonymous');

                $httpBackend.expectGET('/api/auth').respond('{"username":"TestUser"}');
                Auth.init();
                $httpBackend.flush();

                $httpBackend.expectDELETE('/api/auth').respond(500, '');
                Auth.logOut();

                expect(Auth.username()).toEqual('TestUser');
                $httpBackend.flush();
                expect(Auth.username()).toEqual('TestUser');
            });
        });

        describe('requireAnon method', function () {
            it('should redirect authenticated users to AUTH_HOME', inject(function ($location) {
                $location.url(LOGIN_PAGE);
                expect($location.url()).toEqual(LOGIN_PAGE);

                $httpBackend.expectGET('/api/auth').respond('{"username":"TestUser"}');
                Auth.requireAnon();
                $httpBackend.flush();

                expect($location.url()).toEqual(AUTH_HOME);
            }));
        });

        describe('requireAuth method', function () {
            it('should redirect anonymous users to LOGIN_PAGE and redirect back after login', inject(function ($location) {
                var RESTRICTED_PAGE = '/path/to/restricted/page';
                $location.url(RESTRICTED_PAGE);
                expect($location.url()).toEqual(RESTRICTED_PAGE);

                $httpBackend.expectGET('/api/auth').respond(403, '');
                Auth.requireAuth();
                $httpBackend.flush();

                expect($location.url()).toEqual(LOGIN_PAGE);

                $httpBackend.expectPOST('/api/auth').respond('{"username":"TestUser"}');
                Auth.logIn({ username: 'TestUser', password: 'testpassword' });
                $httpBackend.flush();

                expect($location.url()).toEqual(RESTRICTED_PAGE);
            }));
        });
    });

    describe('LoginCtrl controller', function () {
        var controller, scope, $httpBackend, $location;

        beforeEach(function () {
            inject(function($controller, $rootScope, _$httpBackend_, _$location_) {
                scope = $rootScope.$new();
                controller = $controller('LoginCtrl', { $scope: scope });
                $httpBackend = _$httpBackend_;
                $location = _$location_;
            });
        });

        afterEach(function () {
            $httpBackend.verifyNoOutstandingExpectation();
        });

        it('should redirect to AUTH_HOME on successful login', function () {
            scope.form = {
                username: 'TestUser',
                password: 'testpassword',
            };

            $location.url(LOGIN_PAGE);
            expect($location.url()).toEqual(LOGIN_PAGE);

            $httpBackend.expectPOST('/api/auth').respond('{"username":"TestUser"}');
            scope.logIn();
            $httpBackend.flush();

            expect($location.url()).toEqual(AUTH_HOME);
        });

        it('should assign error statuses to form.error', function () {
            scope.form = {
                username: 'TestUser',
                password: 'testpassword',
            };

            spyOn($location, 'url');

            $httpBackend.expectPOST('/api/auth').respond(403, '');
            scope.logIn();
            $httpBackend.flush();

            expect($location.url).not.toHaveBeenCalled();
            expect(scope.form.error).toEqual(403);

            $httpBackend.expectPOST('/api/auth').respond(500, '');
            scope.logIn();
            $httpBackend.flush();

            expect($location.url).not.toHaveBeenCalled();
            expect(scope.form.error).toEqual(500);
        });
    });

    describe('TopBarCtrl controller', function () {
        var controller, scope, $httpBackend, $location;

        beforeEach(function () {
            inject(function($controller, $rootScope, _$httpBackend_, _$location_) {
                scope = $rootScope.$new();
                controller = $controller('TopBarCtrl', { $scope: scope });
                $httpBackend = _$httpBackend_;
                $location = _$location_;
            });
        });

        afterEach(function () {
            $httpBackend.verifyNoOutstandingExpectation();
        });

        it('should redirect to LOGIN_PAGE on successful logout', function () {
            $location.url(AUTH_HOME);
            expect($location.url()).toEqual(AUTH_HOME);

            $httpBackend.expectDELETE('/api/auth').respond(204, '');
            scope.logOut();
            $httpBackend.flush();

            expect($location.url()).toEqual(LOGIN_PAGE);
        });
    });
});
