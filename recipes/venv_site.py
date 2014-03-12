
'''Buildout recipe for adding eggs to a pyvenv virtual environment.

When a buildout environment is bootstrapped/initialized with a venv-style
virtual Python environment, it can be helpful to make the virtual python
interpreter include packages installed in the buildout environment. And
that is exactly what this recipe, based on zc.recipe.egg, does.

Recipe options:

  eggs
      A list of eggs to include in the path given as one or more
      setuptools requirement strings. Each string must be given on a
      separate line.

  extra-paths:
      Extra paths to include in the Python path (.pth) file.

  find-links
      A list of URLs, files, or directories to search for distributions.

  index
      The URL of an index server, or almost any other valid URL. 

  relative-paths:
      If set to true, then egg paths will be generated relative to the
      Python path (.pth) file. This allows a buildout to be moved
      without breaking egg paths. This option can be set in either the
      script section or in the buildout section. 
'''

import itertools
import logging
import os.path
import sys

from zc.buildout.buildout import bool_option
from zc.recipe.egg import Eggs


class VirtualEnvironmentSite(Eggs):
    '''Buildout recipe to add eggs to venv site-packages.'''

    def __init__(self, buildout, name, options):
        super().__init__(buildout, name, options)
        if sys.prefix == sys.base_prefix:
            logging.getLogger(name).warning(
                    "Not in a supported virtual Python environment")
            options['prefix'] = ''
            return
        else:
            options['prefix'] = sys.prefix

        self.extra_paths = [
            os.path.join(buildout['buildout']['directory'], p.strip())
            for p in options.get('extra-paths', '').split('\n') if p.strip()]
        if self.extra_paths:
            options['extra-paths'] = '\n'.join(self.extra_paths)

        self.relative_paths = bool_option(options, 'relative-paths',
                bool_option(buildout['buildout'], 'relative-paths', False))
        if self.relative_paths:
            options['buildout-directory'] = buildout['buildout']['directory']

    def install(self):
        prefix = self.options['prefix']
        if not prefix:
            logging.getLogger(self.name).warning('Skipping site creation.')
            return []
        dist, ws = self.working_set()
        site_path = os.path.join(prefix, 'lib',
                'python{}.{}'.format(*sys.version_info[:2]), 'site-packages',
                'buildout.pth')
        paths = itertools.chain(self.extra_paths, ws.entries)
        if self.relative_paths:
            site_dir = os.path.dirname(site_path)
            paths = (os.path.relpath(path, site_dir) for path in paths)
        with open(site_path, 'w') as file:
            for path in paths:
                file.writelines([path, '\n'])
        return [site_path]

    update = install
