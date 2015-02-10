import re

_LANG = 'en'

_RDF_PREFIX = 'http://rdf.freebase.com/ns/'
_LANG_REGEX = '^"(.*)"@%s$'
_LANG_FALSE_REGEX = '^"(.*)"@(.*)$'

def rdf(name):
    """
    Prepend RDF_PREFIX to name.
    """
    return '%s%s' % (_RDF_PREFIX, name)

def lang(name, lang=_LANG):
    """
    Format name as "<name>"@en. Quotation marks (") in name are escaped.
    """
    return '"%s"@%s' % (name.replace('"', '\\"'), lang)

def _map_clean_rdf_lang(name, lang=_LANG):
    """
    Clean a string by RDF_PREFIX or lang (including quotation marks escaping).
    """
    if name.startswith(_RDF_PREFIX):
        return name[len(_RDF_PREFIX):]
    else:
        r = re.match(_LANG_REGEX % lang, name)
        return r.group(1).replace('\\"', '"') if r else name

def map_clean(obj):
    """
    Return a copy of obj where all fields are cleaned up by RDF or LANG.
    Designed to be used with Python map().
    """
    return type(obj)(*[_map_clean_rdf_lang(i) for i in obj])

def filter_lang(obj, lang=_LANG):
    """
    Return True if all obj fields are in the right lang, False otherwise.
    Designed to be used with Python filter().
    """
    for i in obj:
        r = re.match(_LANG_FALSE_REGEX, i)
        if r and r.group(2) != lang:
            return False
    return True
