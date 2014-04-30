angular.module('openeis-ui.file', [])
.directive('fileUpload', function ($parse) {
    return {
        restrict: 'E',
        template: '<input type="file"><button disabled>Upload</button>',
        compile: function(tElement, tAttr) {
            clickFn = $parse(tAttr.fileUploadClick);

            return function (scope, element, attr) {
                var fileInput = element.find('input'),
                    uploadButton = element.find('button');

                fileInput.on('change', function () {
                    if (fileInput[0].files.length) {
                        uploadButton.prop('disabled', false);
                    } else {
                        uploadButton.prop('disabled', true);
                    }
                });

                uploadButton.on('click', function (event) {
                    scope.$apply(function () {
                        clickFn(scope, {
                            $event: event,
                            fileInput: fileInput,
                        });
                    });
                });
            };
        },
    };
})
// From https://gist.github.com/thomseddon/3511330
.filter('bytes', function() {
    return function(bytes, precision) {
        if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '--';
        if (typeof precision === 'undefined') precision = 0;
        var units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'],
        number = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) + ' ' + units[number];
    };
});
