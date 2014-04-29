describe('openeis-ui.projects', function () {
    var $httpBackend,
        API_URL = '/api';

    beforeEach(function () {
        module('openeis-ui.projects');

        module(function($provide) {
            $provide.constant('API_URL', API_URL);
            $provide.value('projects', []);
            $provide.value('project', {});
            $provide.value('projectFiles', []);
        });

        inject(function (_$httpBackend_) {
            $httpBackend = _$httpBackend_;
        });
    });

    afterEach(function () {
        $httpBackend.verifyNoOutstandingExpectation();
    });

    describe('Projects service', function () {
        var Projects,
            testProjects = [
                { id: 1, name: 'Test project 1' },
                { id: 2, name: 'Test project 2' },
                { id: 3, name: 'Test project 3' },
            ];

        beforeEach(function () {
            inject(function (_Projects_) {
                Projects = _Projects_;
            });
        });

        it('should get projects by project ID that can be saved and deleted', function () {
            var project;

            expect(Projects.get).toBeDefined();

            $httpBackend.expectGET(API_URL + '/projects/' + testProjects[0].id).respond(angular.toJson(testProjects[0]));
            Projects.get(testProjects[0].id).then(function (response) {
                project = response;
            });
            $httpBackend.flush();

            expect(project.id).toEqual(testProjects[0].id);
            expect(project.name).toEqual(testProjects[0].name);
            expect(project.$save).toBeDefined();
            expect(project.$delete).toBeDefined();
        });

        it('should query for all projects', function () {
            var projects;

            expect(Projects.query).toBeDefined();

            $httpBackend.expectGET(API_URL + '/projects').respond(angular.toJson(testProjects));
            Projects.query().then(function (response) {
                projects = response;
            });
            $httpBackend.flush();

            expect(projects.length).toEqual(testProjects.length);

            for (var i = 0; i < testProjects.length; i++) {
                expect(projects[i].id).toEqual(testProjects[i].id);
                expect(projects[i].name).toEqual(testProjects[i].name);
            }
        });

        it('should create new projects', function () {
            var project,
                newProject = { name: 'New project' };

            expect(Projects.create).toBeDefined();

            $httpBackend.expectPOST(API_URL + '/projects').respond(angular.toJson(newProject));
            Projects.create(newProject).then(function (response) {
                project = response;
            });
            $httpBackend.flush();

            expect(project.name).toEqual(newProject.name);
        });
    });

    describe('ProjectFiles service', function () {
        var ProjectFiles,
            testFiles = [
                { id: 1, file: 'File 1' },
                { id: 2, file: 'File 2' },
                { id: 3, file: 'File 3' },
            ];

        beforeEach(function () {
            inject(function (_ProjectFiles_) {
                ProjectFiles = _ProjectFiles_;
            });
        });

        it('should get files by file ID that can be saved and deleted', function () {
            var file;

            expect(ProjectFiles.get).toBeDefined();

            $httpBackend.expectGET(API_URL + '/files/' + testFiles[0].id).respond(angular.toJson(testFiles[0]));
            ProjectFiles.get(testFiles[0].id).then(function (response) {
                file = response;
            });
            $httpBackend.flush();

            expect(file.id).toEqual(testFiles[0].id);
            expect(file.file).toEqual(testFiles[0].file);
            expect(file.$save).toBeDefined();
            expect(file.$delete).toBeDefined();
        });

        it('should query for all files in a project by project ID', function () {
            var files;

            expect(ProjectFiles.query).toBeDefined();

            $httpBackend.expectGET(API_URL + '/files?project=1').respond(angular.toJson(testFiles));
            ProjectFiles.query(1).then(function (response) {
                files = response;
            });
            $httpBackend.flush();

            expect(files.length).toEqual(testFiles.length);

            for (var i = 0; i < testFiles.length; i++) {
                expect(files[i].id).toEqual(testFiles[i].id);
                expect(files[i].file).toEqual(testFiles[i].file);
            }
        });

        it('should retrieve the first rows of a file by file ID', function () {
            var head,
                testHead = {
                    has_header: true,
                    rows: [
                        [ 'Col1', 'Col2', 'Col3' ],
                        [ '1-1', '1-2', '1-3' ],
                        [ '2-1', '2-2', '2-3' ],
                        [ '3-1', '3-2', '3-3' ],
                    ],
                };

            expect(ProjectFiles.head).toBeDefined();

            $httpBackend.expectGET(API_URL + '/files/1/top').respond(angular.toJson(testHead));
            ProjectFiles.head(1).then(function (response) {
                head = response.data;
            });
            $httpBackend.flush();

            expect(head.has_header).toEqual(testHead.has_header);

            for (var i = 0; i < testHead.rows.length; i++) {
                expect(head.rows[i]).toEqual(testHead.rows[i]);
            }
        });
    });

    describe('ProjectsCtrl controller', function () {
        var controller, scope;

        beforeEach(function () {
            inject(function($controller, $rootScope) {
                scope = $rootScope.$new();
                controller = $controller('ProjectsCtrl', { $scope: scope });
            });
        });

        it('should define a function for creating projects', function () {
            var newProject = { name: 'New project' };

            expect(scope.newProject.create).toBeDefined();
            expect(scope.projects.length).toEqual(0);

            scope.newProject.name = newProject.name;
            $httpBackend.expectPOST(API_URL + '/projects').respond(angular.toJson(newProject));
            scope.newProject.create();
            $httpBackend.flush();

            expect(scope.projects.length).toEqual(1);
            expect(scope.projects[0].name).toEqual(newProject.name);
        });

        it('should define a function for renaming projects by array index', inject(function (Projects) {
            var testProject = { id: 1, name: 'Test project' };

            expect(scope.renameProject).toBeDefined();

            // Setup: populate scope.projects
            $httpBackend.expectGET(API_URL + '/projects/' + testProject.id).respond(angular.toJson(testProject));
            Projects.get(testProject.id).then(function (response) {
                scope.projects = [response];
            });
            $httpBackend.flush();

            // Assert original name
            expect(scope.projects[0].name).toEqual(testProject.name);

            testProject.name = 'Test project new';
            spyOn(window, 'prompt').andReturn(testProject.name);

            $httpBackend.expectPUT(API_URL + '/projects/' + testProject.id).respond(angular.toJson(testProject));
            scope.renameProject(0);
            $httpBackend.flush();

            // Assert new name
            expect(scope.projects[0].name).toEqual(testProject.name);
        }));

        it('should define a function for deleting projects by array index', inject(function (Projects) {
            var testProject = { id: 1, name: 'Test project' };

            expect(scope.deleteProject).toBeDefined();

            // Setup: populate scope.projects
            $httpBackend.expectGET(API_URL + '/projects/' + testProject.id).respond(angular.toJson(testProject));
            Projects.get(testProject.id).then(function (response) {
                scope.projects = [response];
            });
            $httpBackend.flush();

            // Assert project exists
            expect(scope.projects[0]).toBeDefined();

            $httpBackend.expectDELETE(API_URL + '/projects/' + testProject.id).respond(204, '');
            scope.deleteProject(0);
            $httpBackend.flush();

            // Assert project deleted
            expect(scope.projects[0]).not.toBeDefined();
        }));
    });

    describe('ProjectCtrl controller', function () {
        var controller, scope;

        beforeEach(function () {
            inject(function($controller, $rootScope) {
                scope = $rootScope.$new();
                controller = $controller('ProjectCtrl', { $scope: scope });
            });
        });

        it('should define a function for uploading files', function () {
            expect(scope.upload).toBeDefined();

            // TODO: refactor $scope.upload to make it more testable
        });

        it('should define a function for deleting files by array index', inject(function (ProjectFiles) {
            var testFile = { id: 1, file: 'test_file.csv' };

            expect(scope.deleteFile).toBeDefined();

            // Setup: populate scope.projectFiles
            $httpBackend.expectGET(API_URL + '/files?project=1').respond(angular.toJson([testFile]));
            ProjectFiles.query(1).then(function (response) {
                scope.projectFiles = response;
            });
            $httpBackend.flush();

            // Assert project file exists
            expect(scope.projectFiles.length).toEqual(1);

            $httpBackend.expectDELETE(API_URL + '/files/' + testFile.id).respond(204, '');
            scope.deleteFile(0);
            $httpBackend.flush();

            // Assert project file deleted
            expect(scope.projectFiles.length).toEqual(0);
        }));
    });
});
