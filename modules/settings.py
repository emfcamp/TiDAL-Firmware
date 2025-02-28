import json

_PATH = "/settings.json"
_settings = None
_modified = False

def load():
    global _settings, _modified
    try:
        with open(_PATH, "r") as f:
            _settings = json.load(f)
    except:
        _settings = {}
    _modified = False

def get(k, default=None):
    if _settings is None:
        load()
    return _settings.get(k, default)

def set(k, v):
    global _modified
    if _settings is None:
        load()
    _settings[k] = v
    _modified = True

def delete(k):
    global _modified
    if _settings is None:
        load()
    del _settings[k]
    _modified = True

def save():
    global _settings, _modified
    if _settings is None:
        load()
    if _modified:
        with open(_PATH, "w") as f:
            json.dump(_settings, f)
        _modified = False
