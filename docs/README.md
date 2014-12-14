# Building the Nodex documentation

Building documentation for packages related to Autodesk can become very tricky because of the dependencies on
`maya` and `pymel` packages which are hard to link to a separate Python installation, or to get Sphinx up and
running within `mayapy.exe`

In my case I was unable to do `mayapy easy_install sphinx` since it would error out on a dependency: `MarkupSafe`.
My workaround was to do an easy install for MarkupSafe into my separate python installation (Python27) and copy over
the installed MarkupSafe folders into mayapy's sitepackages:

So copying over the MarkupSafe related folders from `C:\Python27\Lib\site-packages` to 
`C:\Program Files\Autodesk\Maya2015\Python\Lib\site-packages`.

Unfortunately I haven't found a nicer way to get building sphinx documentation with maya packages so far.
Tips are greatly appreciated!

# Building with mayapy.exe

Once you have the sphinx dependencies installed for mayapy.exe then run `build_docs.py` with it.