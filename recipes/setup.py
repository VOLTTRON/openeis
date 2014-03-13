
from setuptools import setup

setup(
    name = "recipes",
    entry_points = {
        'zc.buildout': ['venv_site = venv_site:VirtualEnvironmentSite'],
    },
    install_requires = ['zc.recipe.egg'],
)
