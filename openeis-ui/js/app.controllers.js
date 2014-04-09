angular.module('openeis-ui.controllers', [])
.controller('LoginCtrl', function ($scope, $location, Auth, $cookies) {
    $scope.form = {};
    $scope.form.logIn = function () {
        Auth.logIn({
            username: $scope.form.username,
            password: $scope.form.password,
        }).then(function () {
            $location.url('/projects');
        }, function (response) {
            switch (response.status) {
                case 401:
                $scope.form.error = 'Authentication failed.'
                break;

                case 405:
                $location.url('/projects');
                break;

                default:
                $scope.form.error = 'Unknown error occurred.'
            }
        });
    };
})
.controller('ProjectsCtrl', function ($scope, Projects) {
    Projects.query(function (results) {
        $scope.projects = results;
    });
})
.controller('ProjectCtrl', function ($scope, $routeParams, Projects) {
    Projects.get({ projectId: $routeParams.projectId }, function (result) {
        $scope.project = result;
    });
})
.controller('TopBarCtrl', function ($scope, Auth, $location) {
    $scope.logOut = function () {
        Auth.logOut().then(function () {
            $location.url('/');
        });
    };
});
