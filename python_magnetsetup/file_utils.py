"""
file utils
"""

def search_paths(MyEnv=None, otype: str = "geom"):
    paths = [ os.getcwd() ]
    if MyEnv:
        default_paths={
            "geom" : MyEnv.yaml_repo,
            "cad" : MyEnv.cad_repo,
            "mesh" : MyEnv.mesh_repo
        }
        paths.append( default_paths[otype] )

    return paths
  
def findfile(searchfile, search_pathes=None):
    """
    Look for file in search_pathes
    """
    import errno

    for path in search_pathes:
        filename = os.path.join(path, searchfile)
        if os.path.isfile(filename):
            print(f"{filename} found in {path}")
            return filename

    # raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), searchfile)
    raise FileNotFoundError(errno.ENOENT, f"cannot find in {search_pathes}", searchfile)

import os
class MyOpen(object):
    """
    Check if `f` is a file name and open the file in `mode`.
    A context manager.
    """
    def __init__(self, f, mode, paths):
        if isinstance(f, str):
            self.file = open(findfile(f, paths), mode)
        else:
            self.file = f

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

