module.exports = function(grunt) {
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    buildDir: 'build',

    clean: {
      build: ['<%= buildDir %>/js/app.ngmin.js'],
    },

    copy: {
      buildHtml: {
        files: [
          { src: ['*.html', 'partials/*.html'], dest: '<%= buildDir %>/' },
        ]
      },
      buildJS: {
        files: [
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/jquery/dist/jquery.*',
              'bower_components/angular-foundation/mm-foundation-tpls.js',
              'bower_components/angular*/angular*.js',
              '!bower_components/angular*/angular*.min.js',
            ],
            dest: '<%= buildDir %>/js/'
          },
        ]
      }
    },

    ngmin: {
      build: {
        files: {
          '<%= buildDir %>/js/app.ngmin.js': 'js/app*.js',
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

    uglify: {
      build: {
        options: {
          sourceMap: true,
        },
        files: {
          '<%= buildDir %>/js/app.js': [
            '<%= buildDir %>/js/angular.js',
            '<%= buildDir %>/js/mm-foundation-tpls.js',
            '<%= buildDir %>/js/*.js',
            '!<%= buildDir %>/js/app.js',
          ],
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
          '<%= buildDir %>/js/app.js',
        ],
      },

      html: {
        files: ['*.html', 'partials/*.html'],
        tasks: ['copy:buildHtml'],
      },

      js: {
        files: ['js/app*.js', '!js/app.ngmin.js'],
        tasks: ['copy:buildJS', 'ngmin', 'uglify', 'clean'],
      },

      sass: {
        files: ['scss/**/*.scss'],
        tasks: ['sass'],
      },
    }
  });

  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-ngmin');
  grunt.loadNpmTasks('grunt-sass');

  grunt.registerTask('build', ['copy', 'sass', 'ngmin', 'uglify', 'clean']);
  grunt.registerTask('default', ['build','watch']);
}
