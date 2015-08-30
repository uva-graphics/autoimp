# autoimp
Automatic Python imports

Overview
--------

The autoimp module imports all available Python modules automatically at the Python interactive prompt, similarly to Matlab:

    >>> from autoimp import *
    >>> os.stat('.')
    >>> Image.open('test.bmp')
    >>> pylab.plot([1,2],[3,4])
    >>> scipy.linalg.eig([[1,2],[3,4]])
    >>> ...

The modules imported from autoimp are proxy objects which lazily load when they are first used.

Python Versions
---------------

The autoimp module has been tested on Python 2.7 and 3.3. It has been updated rarely since it was created in 2006.

License
-------

All related source code and documents are licensed under the [MIT license](http://opensource.org/licenses/MIT).

Installation
------------

To install autoimp, use:

    sudo pip install autoimp

To properly use autoimp, you should set your PYTHONSTARTUP environment variable to point to a .py file containing the following text:

    from autoimp import *

Now, all modules are automatically imported and made available in your interactive Python sessions.
