import epg
import os
import pickle

def set_default_path(path="savefile.bin", org=None, app=None):
    global default_path
    
    dir = epg.system.get_pref_path(org, app) if org and app else ""
    default_path = os.path.join(dir, path)

set_default_path()

def clear(path=None):
    if not path: path = default_path

    os.remove(path)
    
def load(path=None, default=None, error=False):
    if not path: path = default_path

    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)

    except FileNotFoundError as e:
        if default is None:
            raise e
        else:
            return default
    
    else:
        return obj

def dump(obj, path=None):
    if not path: path = default_path

    with open(path, "wb") as f:
        pickle.dump(obj, f)
