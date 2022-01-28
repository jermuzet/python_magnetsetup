"""
file utils
"""
  
def findfile(searchfile, search_pathes=None, mode=None):
    """
    Look for file in search_pathes
    """
    import errno

    for path in search_pathes:
        filename = os.path.join(path, searchfile)
        if os.path.isfile(filename):
            return filename

    raise FileNotFoundError(errno.ENOENT, os.strerror(f"cannot find in {search_pathes}"), searchfile)

import os
class MyOpen(object):
    """
    Check if `f` is a file name and open the file in `mode`.
    A context manager.
    """
    def __init__(self, f, mode, paths):
        for path in paths:
            if isinstance(f, str):
                self.file = open(os.path.join(path, f), mode)
                break
            else:
                self.file = f
        if self.file is f:
            print(f"{f} not found in {paths}")
        self.close_file = (self.file is not f)
    def __enter__(self):
        return self
    def __exit__(self, *args, **kwargs):
        if (not self.close_file):
            return  # do nothing
        # clean up
        exit = getattr(self.file, '__exit__', None)
        if exit is not None:
            return exit(*args, **kwargs)
        else:
            exit = getattr(self.file, 'close', None)
            if exit is not None:
                exit()
    def __getattr__(self, attr):
        return getattr(self.file, attr)
    def __iter__(self):
        return iter(self.file)

