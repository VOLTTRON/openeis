
import sys

# venv and other features used in openeis were introduced in Python 3.3.
if sys.version_info[:2] < (3, 3):
    sys.stderr.write('error: Python 3.3 or greater is required\n')
    sys.exit(1)

import os
import venv

# Install venv and buildout in the buildout directory.
directory = 'buildout'
# Set the prompt in the activate script to (openeis) rather than
# (buildout).
prompt = '(openeis)'

# Install the virtual environment.
builder = venv.EnvBuilder(upgrade=os.path.exists(directory))
_ensure_directories = builder.ensure_directories
def ensure_directories(*args, **kwargs):
    context = _ensure_directories(*args, **kwargs)
    context.prompt = prompt
    return context
builder.ensure_directories = ensure_directories
builder.create(directory)

# Install the buildout environment.
os.system(os.path.join(directory, 'bin', 'python') + ' bootstrap-buildout.py')

