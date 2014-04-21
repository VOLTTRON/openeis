describe('openeis-ui.auth', function () {
    var $location, $httpBackend,
        ANON_HOME = '/path/to/anon/home',
        AUTH_HOME = '/path/to/auth/home';

    beforeEach(function () {
        module('openeis-ui.auth');

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

    describe('Auth service', function () {
        var Auth;

        beforeEach(function () {
            inject(function (_Auth_) {
                Auth = _Auth_;
            });
        });

        describe('isAuthenticated method', function () {
            it('should call the API initially but not subsequently', function () {
                $httpBackend.expectGET('/api/auth').respond(403, '');
                Auth.isAuthenticated();
                $httpBackend.flush();
                $httpBackend.verifyNoOutstandingExpectation();

                Auth.isAuthenticated();
            });

            it('should update the username property', function () {
                $httpBackend.expectGET('/api/auth').respond('{"username":"TestUser"}');
                Auth.isAuthenticated();

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
        });

        describe('relocate method', function () {
            it('should redirect anonymous users to ANON_HOME', function () {
                $location.currentPath = '/not' + ANON_HOME;

                $httpBackend.expectGET('/api/auth').respond(403, '');
                Auth.relocate();
                $httpBackend.flush();

                expect($location.path).toHaveBeenCalled();
                expect($location.url).toHaveBeenCalledWith(ANON_HOME);
            });

            it('should not redirect anonymous users redundantly', function () {
                $location.currentPath = ANON_HOME;

                $httpBackend.expectGET('/api/auth').respond(403, '');
                Auth.relocate();
                $httpBackend.flush();

                expect($location.path).toHaveBeenCalled();
                expect($location.url).not.toHaveBeenCalled();
            });

            it('should redirect authenticated users from ANON_HOME to AUTH_HOME', function () {
                $location.currentPath = ANON_HOME;

                $httpBackend.expectGET('/api/auth').respond('{"username":"TestUser"}');
                Auth.relocate();
                $httpBackend.flush();

                expect($location.path).toHaveBeenCalled();
                expect($location.url).toHaveBeenCalledWith(AUTH_HOME);
            });

            it('should not redirect authenticated users redundantly', function () {
                $location.currentPath = AUTH_HOME;

                $httpBackend.expectGET('/api/auth').respond('{"username":"TestUser"}');
                Auth.relocate();
                $httpBackend.flush();

                expect($location.path).toHaveBeenCalled();
                expect($location.url).not.toHaveBeenCalled();
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
