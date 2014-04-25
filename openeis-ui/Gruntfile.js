module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    buildDir: 'build',

    clean: {
      build: ['<%= buildDir %>'],
    },

    concat: {
      options: {
        process: function(src) {
          return src.replace(/^\/\/# sourceMappingURL=.+\n/mg, '');
        },
      },
      build: {
        files : {
          '<%= buildDir %>/js/app.min.js': [
            'bower_components/angular/angular.min.js',
            'bower_components/angular-*/angular-*.min.js',
            'bower_components/ng-file-upload/angular-file-upload.min.js',
            'bower_components/angular-foundation/mm-foundation-tpls.min.js',
            '<%= buildDir %>/js/app.min.js',
          ],
        }
      }
    },

    karma: {
      build: {
        configFile: 'karma.conf.js',
        background: true,
      },
    },

    ngmin: {
      build: {
        files: {
          '<%= buildDir %>/js/app.js': [
            'js/*.js',
            '!js/*.spec.js',
          ]
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

    focus: {
      notest: {
        exclude: ['karma'],
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
        files: ['js/*.js', '!js/*.spec.js'],
        tasks: ['ngmin', 'uglify', 'concat'],
      },

      karma: {
        files: ['js/*.js'],
        tasks: ['karma:build:run'],
      },

      sass: {
        files: ['scss/**/*.scss'],
        tasks: ['sass'],
      },
    }
  });

  grunt.loadNpmTasks('grunt-angular-templates');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-focus');
  grunt.loadNpmTasks('grunt-karma');
  grunt.loadNpmTasks('grunt-ngmin');
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-sync');

  grunt.registerTask('build', ['clean', 'sass', 'sync', 'ngmin', 'ngtemplates', 'uglify', 'concat']);
  grunt.registerTask('notest', ['build', 'focus:notest']);
  grunt.registerTask('default', ['karma:build:start', 'build', 'watch']);
};
