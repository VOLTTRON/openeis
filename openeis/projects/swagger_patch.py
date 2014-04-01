'''Monkey patch for rest-framework-swagger introspectors.

Swagger attempts to access func_code and func_closure on methods which
were renamed to __code__ and __closure__ in Python 3. Importing this
module patches ViewSetIntrospector._resolve_methods to use the Python 3
names.
'''

try:
    from rest_framework_swagger.introspectors import ViewSetIntrospector
except ImportError:
    pass
else:
    def _resolve_methods(self):
        callback = self.pattern.callback
        try:
            closure = callback.__closure__
            freevars = callback.__code__.co_freevars
        except AttributeError:
            raise RuntimeError('Unable to use callback invalid closure/function specified.')
        return closure[freevars.index('actions')].cell_contents
    ViewSetIntrospector._resolve_methods = _resolve_methods
