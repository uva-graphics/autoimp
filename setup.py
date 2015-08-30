# Release instructions: https://packaging.python.org/en/latest/distributing.html
#  % rm -rf dist
#  % python setup.py sdist
#  % twine upload dist/*

"""A setuptools based setup module."""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(
    name='autoimp',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='1.0.4',

    description='Automatic Python imports',
    long_description="""
    The autoimp module makes usage of the interactive Python prompt more productive.
    With autoimp, all installed Python modules can be imported with the single statement "from autoimp import *".  The  imported modules are proxy objects which lazily load when first used.

    Install with 'sudo pip install autoimp'. 

    Proper installation of autoimp involves placing "from autoimp import *" in your
    PYTHONSTARTUP file. Once autoimp is properly installed, it is no longer necessary to use statements of the form "import X" at the interactive prompt.
    """,

    # The project's main homepage.
    url='https://github.com/uva-graphics/autoimp',

    # Author details
    author='Connelly Barnes',
    author_email='connellybarnes at yahoo.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    # What does your project relate to?
    keywords='interactive interpreter development imports convenience',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['autoimp']
)
