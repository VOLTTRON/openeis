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
.controller('ProjectsCtrl', function ($scope, projects) {
    $scope.projects = projects;
})
.controller('ProjectCtrl', function ($scope, project) {
    $scope.project = project;
})
.controller('TopBarCtrl', function ($scope, Auth, $location) {
    $scope.logOut = function () {
        Auth.logOut().then(function () {
            $location.url('/');
        });
    };
});
