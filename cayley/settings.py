from __future__ import absolute_import
import os
from importlib import import_module

def load_settings():
    if "PYTHON_CAYLEY_SETTINGS" in os.environ:
        path = os.environ["PYTHON_CAYLEY_SETTINGS"]
    elif os.path.isfile('settings.py'):
        path = 'settings'
        os.environ["PYTHON_CAYLEY_SETTINGS"] = path
    else:
        return Settings()

    mod = import_module(path)
    return Settings(mod)
 

class Settings(object):
    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            mod = args[0]
            self.PROTO = getattr(mod, 'CAYLEY_PROTO', 'http')
            self.PORT  = getattr(mod, 'CAYLEY_PORT', '64210')
            self.HOST  = getattr(mod, 'CAYLEY_HOST', 'localhost')
            self.VERSION  = getattr(mod, 'CAYLEY_VERSION', 'v1')
        else:
            self.PROTO = kwargs.get('CAYLEY_PROTO', 'http')
            self.PORT  = kwargs.get('CAYLEY_PORT', '64210')
            self.HOST  = kwargs.get('CAYLEY_HOST', 'localhost')
            self.VERSION  = kwargs.get('CAYLEY_VERSION', 'v1')

    @property
    def QUERY_URL(self):
        return "%s://%s:%s/api/%s/query/gremlin" % (self.PROTO, self.HOST, self.PORT, self.VERSION)

settings = load_settings()