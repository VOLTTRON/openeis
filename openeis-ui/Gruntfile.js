module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    buildDir: '../openeis/static_ui/',

    copy: {
      build: {
        files: [
          { src: ['*.html', 'partials/*.html'], dest: '<%= buildDir %>' },
        ]
      }
    },

    ngmin: {
      build: {
        files: {
          'js/app.ngmin.js': 'js/app.js',
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
        '<%= buildDir %>css/app.css': 'scss/app.scss',
        },
      },
    },

    uglify: {
      build: {
        options: {
          sourceMap: true,
          sourceMapIncludeSources: true,
        },
        files: {
          '<%= buildDir %>js/app.js': [
            'bower_components/angular/angular.js',
            'bower_components/angular-*/angular-*.js',
            '!bower_components/angular-*/angular-*.min.js',
            'js/app.ngmin.js',
          ]
        },
      },
    },

    watch: {
      grunt: { files: ['Gruntfile.js'] },

      livereload: {
        options: { livereload: true },
        files: [
          '<%= buildDir %>*.html',
          '<%= buildDir %>css/*',
          '<%= buildDir %>js/*',
          '<%= buildDir %>partials/*.html',
        ],
      },

      html: {
        files: ['*.html', 'partials/*.html'],
        tasks: ['copy'],
      },

      js: {
        files: ['js/app.js'],
        tasks: ['ngmin', 'uglify'],
      },

      sass: {
        files: ['scss/**/*.scss'],
        tasks: ['sass'],
      },
    }
  });

  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-ngmin');
  grunt.loadNpmTasks('grunt-sass');

  grunt.registerTask('build', ['copy', 'sass', 'ngmin', 'uglify']);
  grunt.registerTask('default', ['build','watch']);
}
