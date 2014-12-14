Installation
============

This is a brief 3-step overview of how you could install the nodex package and get started right away!


Get the package from the repository
-----------------------------------

Pick one of the two choices below:

- `Download the latest master archive (.zip) <https://github.com/BigRoy/nodex/archive/master.zip>`_
- `Clone the nodex GitHub repository <https://github.com/BigRoy/nodex>`_

If you choose to download the *.zip* file feel free to unpack to a location of your choice and proceed to the next
step.

Installing Nodex
----------------

Within the downloaded directory there should be a python package called ``nodex``.
The *package* is the ``nodex`` directory that directly contains a ``__init__.py`` file.

The easiest way to install is to copy the *PACKAGE* into your maya scripts folder.

============================ ==========================================================================
OS                           Default Path
============================ ==========================================================================
Windows XP                   ``\Documents and Settings\<username>\My Documents\maya\<version>\scripts``
---------------------------- --------------------------------------------------------------------------
Windows Vista/7              ``\Users\<username>\Documents\maya\<version>\scripts``
---------------------------- --------------------------------------------------------------------------
Mac                          ``~<username>/Library/Preferences/Autodesk/maya/<version>/scripts``
---------------------------- --------------------------------------------------------------------------
Linux (64-bit)               ``~<username>/maya/<version>/scripts``
============================ ==========================================================================

| *username*: The user account that has Maya installed on the computer
| *version*: The version of Maya you want to install the scripts for, e.g. *2015-x64*
|

Note that all that is required for the ``nodex`` package to work is to place it in a position that is in
``sys.path`` for Python. If your studio uses Maya.env or any other way to add scripts folder to Maya feel free to position the package in there.

Testing the installation
------------------------

If the following code runs in a Python tab in your Autodesk Maya script editor the *nodex* package should
be installed correctly.

.. code-block:: python

    from nodex.core import Nodex


Everything should be ready to go.
Next up: :doc:`getting_started`