describe('openeis-ui.projects', function () {
    var $httpBackend,
        API_URL = '/api';

    beforeEach(function () {
        module('openeis-ui.projects');

        module(function($provide) {
            $provide.constant('API_URL', API_URL);
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

        it('should define get, query, and create methods', function () {
            expect(Projects.get).toBeDefined();
            expect(Projects.query).toBeDefined();
            expect(Projects.create).toBeDefined();
        });

        it('should get projects by project ID that can be saved and deleted', function () {
            var project;

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

        it('should define query and head methods', function () {
            expect(ProjectFiles.query).toBeDefined();
            expect(ProjectFiles.head).toBeDefined();
        });

        it('should query for all files in a project by project ID', function () {
            var files;

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
});
