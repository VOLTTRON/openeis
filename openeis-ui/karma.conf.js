module.exports = function(config) {
  config.set({
    frameworks: ['jasmine'],
    browsers: ['Chrome', 'Firefox', 'PhantomJS'],
    files: [
      'bower_components/angular/angular.js',
      'bower_components/angular-*/angular-*.js',
      'bower_components/ng-file-upload/angular-file-upload.js',
      'js/*.js',
    ],
  });
};
