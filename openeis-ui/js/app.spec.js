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

    it('should define the constant LOGIN_PAGE', inject(function (LOGIN_PAGE) {
        expect(LOGIN_PAGE).toBeDefined();
    }));

    it('should define the constant AUTH_HOME', inject(function (AUTH_HOME) {
        expect(AUTH_HOME).toBeDefined();
    }));
});
