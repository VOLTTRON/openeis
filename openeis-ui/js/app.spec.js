describe('openeis-ui', function () {
    var Auth;

    // Mock templates module
    angular.module('openeis-ui.templates', []);

    beforeEach(function () {
        module('openeis-ui');

        module(function($provide) {
            Auth = {
                relocate: jasmine.createSpy('relocate'),
            };

            $provide.value('Auth', Auth);
        });
    });

    it('should define the constant API_URL', inject(function (API_URL) {
        expect(API_URL).toBeDefined();
    }));

    it('should define the constant ANON_HOME', inject(function (ANON_HOME) {
        expect(ANON_HOME).toBeDefined();
    }));

    it('should define the constant AUTH_HOME', inject(function (AUTH_HOME) {
        expect(AUTH_HOME).toBeDefined();
    }));
});
