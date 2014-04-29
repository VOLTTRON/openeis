angular.module('openeis-ui.projects', [
    'openeis-ui.auth', 'openeis-ui.file',
    'ngResource', 'angularFileUpload',
])
.config(function (authRouteProvider) {
    authRouteProvider
        .whenAuth('/projects', {
            controller: 'ProjectsCtrl',
            templateUrl: 'partials/projects.html',
            resolve: {
                projects: ['Projects', function(Projects) {
                    return Projects.query();
                }]
            },
        })
        .whenAuth('/projects/:projectId', {
            controller: 'ProjectCtrl',
            templateUrl: 'partials/project.html',
            resolve: {
                project: ['Projects', '$route', function(Projects, $route) {
                    return Projects.get($route.current.params.projectId);
                }],
                projectFiles: ['ProjectFiles', '$route', function(ProjectFiles, $route) {
                    return ProjectFiles.query($route.current.params.projectId);
                }],
            },
        });
})
.factory('Projects', function ($resource, API_URL) {
    var resource = $resource(API_URL + '/projects/:projectId', { projectId: '@id' }, {
        create: { method: 'POST' },
        save: { method: 'PUT' },
    });

    return {
        get: function (projectId) {
            return resource.get({ projectId: projectId}).$promise;
        },
        query: function () {
            return resource.query().$promise;
        },
        create: function (project) {
            return resource.create(project).$promise;
        },
    };
})
.factory('ProjectFiles', function ($resource, API_URL, $http) {
    var resource = $resource(API_URL + '/files/:fileId', { fileId: '@id' });

    return {
        get: function (fileId) {
            return resource.get({ fileId: fileId }).$promise;
        },
        query: function (projectId) {
            return resource.query({ project: projectId }).$promise;
        },
        head: function (fileId) {
            return $http({
                method: 'GET',
                url: API_URL + '/files/' + fileId + '/top',
                transformResponse: angular.fromJson,
            });
        },
    };
})
.controller('ProjectsCtrl', function ($scope, projects, Projects) {
    $scope.projects = projects;

    $scope.newProject = {
        name: '',
        create: function () {
            Projects.create({ name: $scope.newProject.name }).then(function (response) {
                $scope.newProject.name = '';
                $scope.projects.push(response);
            });
        },
    };

    $scope.renameProject = function ($index) {
        var newName = prompt("New project name:");

        if (!newName || !newName.length) {
            return;
        }

        $scope.projects[$index].name = newName;
        $scope.projects[$index].$save(function (response) {
            $scope.projects[$index] = response;
        });
    };

    $scope.deleteProject = function ($index) {
        $scope.projects[$index].$delete(function () {
            $scope.projects.splice($index, 1);
        });
    };
})
.controller('ProjectCtrl', function ($scope, project, projectFiles, $upload, API_URL, ProjectFiles) {
    $scope.project = project;
    $scope.projectFiles = projectFiles;

    function openModal (file) {
        $scope.modal = {
            show: true,
            file: file,
        };
    }

    $scope.upload = function (fileInput) {
        angular.forEach(fileInput[0].files, function(file) {
            $upload.upload({
                url: API_URL + '/projects/' + project.id + '/add_file',
                file: file,
            }).then(function (response) {
                ProjectFiles.head(response.data.id).then(function (headResponse) {
                    if (headResponse.data.has_header) {
                        headResponse.data.header = headResponse.data.rows.shift();
                    }
                    response.data.head = headResponse.data;
                    openModal(response.data);
                });

                ProjectFiles.get(response.data.id).then(function (response) {
                    $scope.projectFiles.push(response);
                });

                fileInput.val('').triggerHandler('change');
            });
        });
    };

    $scope.deleteFile = function ($index) {
        $scope.projectFiles[$index].$delete(function () {
            $scope.projectFiles.splice($index, 1);
        });
    };
});
