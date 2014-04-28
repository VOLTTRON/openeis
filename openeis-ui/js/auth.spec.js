describe('openeis-ui.auth', function () {
    var provider, $location, $httpBackend,
        ANON_HOME = '/path/to/anon/home',
        AUTH_HOME = '/path/to/auth/home';

    beforeEach(function () {
        module('openeis-ui.auth', function (authRouteProvider) {
            provider = authRouteProvider;
        });

        $location = {
            currentPath: '',
            path: function () { return $location.currentPath; },
            url: jasmine.createSpy('url'),
        };

        spyOn($location, 'path').andCallThrough();

        module(function($provide) {
            $provide.constant('API_URL', '/api');
            $provide.constant('$location', $location);
            $provide.constant('ANON_HOME', ANON_HOME);
            $provide.constant('AUTH_HOME', AUTH_HOME);
        });

        inject(function (_$httpBackend_) {
            $httpBackend = _$httpBackend_;
        });
    });

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
    });

    describe('authRoute provider', function () {
        describe('whenAnon method', function () {
            it('should add an anon resolve', function () {
                inject(function (authRoute) {
                    expect(authRoute.routes['/anon-test']).not.toBeDefined();

                    provider.whenAnon('/anon-test', {});

                    expect(authRoute.routes['/anon-test'].resolve.anon).toBeDefined();
                });
            });

            it('should be chainable', function () {
                inject(function (authRoute) {
                    expect(authRoute.routes['/anon-test']).not.toBeDefined();
                    expect(authRoute.routes['/anon-test-2']).not.toBeDefined();
                    expect(authRoute.routes['/auth-test']).not.toBeDefined();

                    provider
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

                    provider.whenAuth('/auth-test', {});

                    expect(authRoute.routes['/auth-test'].resolve.auth).toBeDefined();
                });
            });

            it('should be chainable', function () {
                inject(function (authRoute) {
                    expect(authRoute.routes['/auth-test']).not.toBeDefined();
                    expect(authRoute.routes['/auth-test-2']).not.toBeDefined();
                    expect(authRoute.routes['/anon-test']).not.toBeDefined();

                    provider
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
        var Auth;

        beforeEach(function () {
            inject(function (_Auth_) {
                Auth = _Auth_;
            });
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
            it('should redirect authenticated users to AUTH_HOME', function () {
                $httpBackend.expectGET('/api/auth').respond('{"username":"TestUser"}');
                Auth.requireAnon();
                $httpBackend.flush();

                expect($location.url).toHaveBeenCalledWith(AUTH_HOME);
            });
        });

        describe('requireAuth method', function () {
            it('should redirect anonymous users to ANON_HOME', function () {
                $httpBackend.expectGET('/api/auth').respond(403, '');
                Auth.requireAuth();
                $httpBackend.flush();

                expect($location.url).toHaveBeenCalledWith(ANON_HOME);
            });
        });
    });

    describe('LoginCtrl controller', function () {
        var controller, scope;

        beforeEach(function () {
            inject(function($controller, $rootScope) {
                scope = $rootScope.$new();
                controller = $controller('LoginCtrl', { $scope: scope });
            });
        });

        it('should define a function for logging in', function () {
            expect(scope.form.logIn).toBeDefined();
        });

        it('should redirect to AUTH_HOME on successful login', function () {
            scope.form.username = 'TestUser';
            scope.form.password = 'testpassword';
            $httpBackend.expectPOST('/api/auth').respond('{"username":"TestUser"}');
            scope.form.logIn();
            $httpBackend.flush();

            expect($location.url).toHaveBeenCalledWith(AUTH_HOME);
        });

        it('should display an error message for invalid credentials', function () {
            scope.form.username = 'TestUser';
            scope.form.password = 'testpassword';
            $httpBackend.expectPOST('/api/auth').respond(403, '');
            scope.form.logIn();
            $httpBackend.flush();

            expect($location.url).not.toHaveBeenCalled();
            expect(scope.form.error).toEqual('Authentication failed.');
        });

        it('should display an error message for unrecognized responses from the API', function () {
            scope.form.username = 'TestUser';
            scope.form.password = 'testpassword';
            $httpBackend.expectPOST('/api/auth').respond(500, '');
            scope.form.logIn();
            $httpBackend.flush();

            expect($location.url).not.toHaveBeenCalled();
            expect(scope.form.error).toEqual('Unknown error occurred.');
        });
    });

    describe('TopBarCtrl controller', function () {
        var controller, scope;

        beforeEach(function () {
            inject(function($controller, $rootScope) {
                scope = $rootScope.$new();
                controller = $controller('TopBarCtrl', { $scope: scope });
            });
        });

        it('should define a function for logging out', function () {
            expect(scope.logOut).toBeDefined();
        });

        it('should redirect to ANON_HOME on successful logout', function () {
            $httpBackend.expectDELETE('/api/auth').respond(204, '');
            scope.logOut();
            $httpBackend.flush();

            expect($location.url).toHaveBeenCalledWith(ANON_HOME);
        });
    });
});
