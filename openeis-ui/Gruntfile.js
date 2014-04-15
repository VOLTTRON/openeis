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
            '<%= buildDir %>/js/jquery.min.js',
            '<%= buildDir %>/js/angular.min.js',
            '<%= buildDir %>/js/*.js',
            '!<%= buildDir %>/js/app.min.js',
          ],
        }
      }
    },

    ngmin: {
      build: {
        files: {
          '<%= buildDir %>/js/app.js': 'js/app*.js',
        },
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
          { src: ['*.html', 'partials/*.html'], dest: '<%= buildDir %>/' },
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/jquery/dist/jquery.min.js',
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
          '<%= buildDir %>/js/app.js': '<%= buildDir %>/js/app.js',
        },
      },
    },

    watch: {
      grunt: { files: ['Gruntfile.js'] },

      livereload: {
        options: { livereload: true },
        files: [
          '<%= buildDir %>/**/*.html',
          '<%= buildDir %>/css/app.css',
          '<%= buildDir %>/js/app.min.js',
        ],
      },

      html: {
        files: ['*.html', 'partials/*.html'],
        tasks: ['sync'],
      },

      js: {
        files: ['js/app*.js', '!js/app.ngmin.js'],
        tasks: ['ngmin', 'uglify', 'sync', 'concat'],
      },

      sass: {
        files: ['scss/**/*.scss'],
        tasks: ['sass'],
      },
    }
  });

  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-ngmin');
  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-sync');

  grunt.registerTask('build', ['sass', 'ngmin', 'uglify', 'sync', 'concat']);
  grunt.registerTask('default', ['build','watch']);
};
