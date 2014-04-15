module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    buildDir: 'build',

    concat: {
      options: {
        process: function(src) {
          return src.replace(/^\/\/# sourceMappingURL=.+\n/mg, '');
        },
      },
      build: {
        files : {
          '<%= buildDir %>/js/app.min.js': [
            '<%= buildDir %>/js/angular.min.js',
            '<%= buildDir %>/js/angular-*.min.js',
            '<%= buildDir %>/js/mm-foundation-tpls.min.js',
            '<%= buildDir %>/js/app.min.js',
          ],
        }
      }
    },

    ngmin: {
      build: {
        files: {
          '<%= buildDir %>/js/app.js': ['js/app.js', 'js/app.*.js']
        },
      },
    },

    ngtemplates: {
      options: {
        module: 'openeis-ui.templates',
        htmlmin: {
          collapseBooleanAttributes:      true,
          collapseWhitespace:             true,
          removeAttributeQuotes:          true,
          removeComments:                 true, // Only if you don't use comment directives!
          removeEmptyAttributes:          true,
          removeScriptTypeAttributes:     true,
          removeStyleLinkTypeAttributes:  true,
        },
        prefix: '/',
        standalone: true,
      },
      build: {
        src: 'partials/*.html',
        dest: '<%= buildDir %>/js/app.templates.js',
      },
    },

    sass: {
      options: {
        includePaths: ['bower_components/foundation/scss'],
        outputStyle: 'compressed',
      },
      build: {
        files: {
        '<%= buildDir %>/css/app.css': 'scss/app.scss',
        },
      },
    },

    sync: {
      build: {
        files: [
          { src: 'index.html', dest: '<%= buildDir %>/' },
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/angular-foundation/mm-foundation-tpls.min.js',
              'bower_components/ng-file-upload/angular-file-upload.min.js',
              'bower_components/angular*/angular*.min.js',
            ],
            dest: '<%= buildDir %>/js/'
          },
        ]
      }
    },

    uglify: {
      build: {
        files: {
          '<%= buildDir %>/js/app.min.js': [
            '<%= buildDir %>/js/app.js',
            '<%= buildDir %>/js/app.templates.js',
          ],
        },
      },
    },

    watch: {
      grunt: { files: ['Gruntfile.js'] },

      livereload: {
        options: { livereload: true },
        files: [
          '<%= buildDir %>/index.html',
          '<%= buildDir %>/css/app.css',
          '<%= buildDir %>/js/app.min.js',
        ],
      },

      index: {
        files: ['index.html'],
        tasks: ['sync'],
      },

      partials: {
        files: ['partials/*.html'],
        tasks: ['ngtemplates', 'uglify', 'concat'],
      },

      js: {
        files: ['js/app*.js'],
        tasks: ['sync', 'ngmin', 'uglify', 'concat'],
      },

      sass: {
        files: ['scss/**/*.scss'],
        tasks: ['sass'],
      },
    }
  });

  grunt.loadNpmTasks('grunt-angular-templates');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-ngmin');
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-sync');

  grunt.registerTask('build', ['sass', 'sync', 'ngmin', 'ngtemplates', 'uglify', 'concat']);
  grunt.registerTask('default', ['build','watch']);
};
