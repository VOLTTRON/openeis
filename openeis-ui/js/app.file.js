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
});
