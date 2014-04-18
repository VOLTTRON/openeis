'''Package-level settings with package defaults.'''

from django.conf import settings as _settings

__all__ = ('settings',)

_DEFAULTS = {
    'FILE_HEAD_ROWS_DEFAULT': 15,
    'FILE_HEAD_ROWS_MAX': 30,
}


class Settings(object):
    '''Package-level settings providing default values.

    Initializes settings to the package defaults, then updates the
    settings from the OPENEIS_PROJECTS dictionary in
    django.conf.settings.
    '''
    __slots__ = ('__dict__', '__weakref__')

    def __init__(self):
        dct = _DEFAULTS.copy()
        dct.update({key: value for key, value in
                    getattr(_settings, 'OPENEIS_PROJECTS', {}).items()
                    if key.isupper() and not key.startswith('_')})
        self.__dict__ = dct


settings = Settings()
