from .settings import settings
import requests, re
from collections import namedtuple, Iterable, Callable

def _render_param(data):
    if data is None:
        return ''
    elif isinstance(data,basestring):
        # return '"%s"'%re.sub(r'(\\?)"',r'\1\1\"',data)
        return '"%s"'%re.sub(r'(\\?)"',r'\"',data)
        # return '"%s"'%re.sub(r'"',r'\"',data)
    elif isinstance(data,GremlinQuery):
        return data._make_query()
    elif isinstance(data,(int,long)):
        return '%d'%data
    elif isinstance(data,Iterable):
        return '[%s]'%(', '.join(_render_param(i) for i in data))
    else:
        return '"%r"'%data

def _extract_param(data):
    if data is None:
        return []
    elif isinstance(data,basestring):
        return [data]
    elif isinstance(data,Iterable):
        return list(data)
    else:
        return ['%r'%data]

class GraphObject(object):
    def V(self, *args, **kwargs):
        return Vertex(self, *args, **kwargs)

    def Vertex(self, *args, **kwargs):
        return self.V(*args, **kwargs)

    def M(self):
        return Morphism(self)

    def Morphism(self):
        return self.M()

    def Emit(self, data):
        raise NotImplementedError

    def _make_query(self):
        return "g"

    def _make_tags(self):
        return []

    def _get_pyop(self):
        return []

class _meta(object):
    def __init__(self,Meta = None):
        self.__meta = Meta or object()

    def get(self,key,default):
        return getattr(self.__meta,key,default)

    def __getattr__(self,key):
        return self.get(key,None)

class GremlinQueryMeta(type):
    def __init__(cls,name,parent,dct):
        try:
            cls._meta = _meta(dct['Meta'])
        except KeyError:
            cls._meta = _meta()
        
        if not hasattr(cls,'registry'):
            cls.registry = {}
            cls._GremlinQuery__abstract = True
        else:
            if cls._meta.get('abstract',False):
                cls._GremlinQuery__abstract = True
                cls._GremlinQuery__call_name = ''
            else:
                cls.registry[name] = cls
                for n in cls._meta.get('alias',[]):
                    cls.registry[n] = cls
                cls._GremlinQuery__abstract = False
                cls._GremlinQuery__call_name = name

        cls._GremlinQuery__terminal = cls._meta.get('terminal',False)

class GremlinQuery(object):
    __metaclass__ = GremlinQueryMeta

    def __init__(self, predecessor, *args):
        if self.__abstract:
            raise NotImplementedError("Cannot instatiate a GremlinQuery class. Only subclasses could be instatiated")
        self.__validate_args(args)
            
        self.__predecessor = predecessor
        self.params = "(%s)"%(", ".join(_render_param(i) for i in args))
        if hasattr(self,"Meta") and hasattr(self.Meta,"tag"):
            tag = self.Meta.tag
            if isinstance(tag,tuple):
                tags = args[tag[0]:tag[1]]
                self.tags = _extract_param(tags)
            else:
                try:
                    tags = args[tag]
                except IndexError:
                    tags = None
                self.tags = _extract_param(tags)
        else:
            self.tags = []
        require_morphism = self._meta.require_morphism
        if require_morphism is not None:
            if isinstance(require_morphism,(int,long)):
                require_morphism = [require_morphism]
            for i in require_morphism:
                self.tags += args[i]._make_tags()

    def __validate_args(self,args):
        if self._meta.min_args is not None and len(args) < self._meta.min_args:
            raise TypeError("%s() takes at least %d args, received %d"%\
                (self.__call_name,self._meta.min_args,len(args)))
        if self._meta.max_args is not None and len(args) > self._meta.max_args:
            raise TypeError("%s() takes at most %d args, received %d"%\
                (self.__call_name,self._meta.max_args,len(args)))
        val = self._meta.args_val
        if val is not None:
            if not isinstance(val[0],Iterable):
                val = [val]
            for arg, check in val:
                try:
                    if not isinstance(args[arg],check):
                        raise TypeError("%s() take %s as %dth arg"%\
                            (self.__call_name,check,arg))
                except IndexError:
                    pass

        require_morphism = self._meta.require_morphism
        if require_morphism is not None:
            if isinstance(require_morphism,(int,long)):
                require_morphism = [require_morphism]
            for i in require_morphism:
                try:
                    if not args[i].isMorphism():
                        raise TypeError("%s() require a Morphism as %dth arg"%\
                            (self.__call_name,check,arg))
                except IndexError:
                    pass
                except AttributeError:
                    raise TypeError("%s() require a Morphism as %dth arg"%\
                        (self.__call_name,check,arg))

    def __iter__(self):
        return iter(self.__query_or_cache())

    def __getitem__(self,key):
        return self.__query_or_cache().__getitem__(key)

    def __len__(self):
        return len(self.__query_or_cache())

    def __repr__(self):
        if self.__terminal and not self.isMorphism():
            return str(self.__query_or_cache())
        else:
            return self._make_query()

    __cache = None
    def __query_or_cache(self):
        if not self.__terminal and self.isMorphism():
            raise TypeError("This is not a terminal query")
        if self.__cache is None:
            query = self._make_query()
            tags  = self._make_tags()
            pyop = self._get_pyop()
            self.__cache = self.__exec_query(query, tags, pyop)
        return self.__cache

    def __exec_query(self,query,tags, pyop):
        CayleyResult = namedtuple("CayleyResult", set(tags))
        r = requests.post(settings.QUERY_URL,data = query.encode('utf-8'))
        if r.status_code != 200:
            try:
                error = "Error(%d) - %s"%(r.status_code,r.json()['error'])
            except:
                error = "Error(%d)"%(r.status_code)
            raise Exception(error)
        try:
            result = r.json()['result']
        except KeyError:
            try:
                error = "Error(%d) - %s"%(r.status_code,r.json()['error'])
            except:
                error = "Error(%d) - 'result' not received"%(r.status_code)
            raise Exception(error)

        if result is None:
            return []
        cbs = [i for i in pyop if isinstance(i,Callable)]
        opts = set(i for i in pyop if isinstance(i,basestring))
        distinct = set if 'distinct' in opts else list

        ret = distinct(CayleyResult(**i) for i in result)

        for cb in cbs:
            ret = cb(ret)

        return ret

    def _make_query(self):
        return "%s.%s%s"%(self.__predecessor._make_query(),self.__call_name,self.params)

    def _make_tags(self):
        return self.tags + self.__predecessor._make_tags()

    def _get_pyop(self):
        return self.__predecessor._get_pyop()

    def __getattr__(self,attr):
        if self.__terminal:
            raise AttributeError("'%s' as no attribute '%s'"%(type(self),attr))
        try:
            cls = self.registry[attr]
        except KeyError:
            raise AttributeError("'%s' as no attribute '%s'"%(type(self),attr))
        def call(*args):
            return cls(self,*args)

        return call

    def isMorphism(self):
        return self.__predecessor.isMorphism()

class PythonQuery(GremlinQuery):
    class Meta:
        abstract = True

    def __init__(self, predecessor):
        # don't call super but manage here
        if self._GremlinQuery__abstract:
            raise NotImplementedError("Cannot instatiate a GremlinQuery class. Only subclasses could be instatiated")
        self.__predecessor = predecessor

    def _make_query(self):
        return self.__predecessor._make_query()

    def _make_tags(self):
        return self.__predecessor._make_tags()

    def _get_pyop(self):
        return self.__predecessor._get_pyop()+self._pyop

# Paths
class Vertex(GremlinQuery):
    def __init__(self,*args):
        super(Vertex,self).__init__(*args)
        self.tags = ['id']

    def isMorphism(self):
        return False

class Morphism(GremlinQuery):
    def __init__(self,*args):
        super(Morphism,self).__init__(*args)
        self.tags = ['id']

    def isMorphism(self):
        return True

class In(GremlinQuery):
    pass
    class Meta:
        tag = 1
        max_args=2

class Out(GremlinQuery):
    pass
    class Meta:
        tag = 1
        max_args=2

class Both(GremlinQuery):
    pass
    class Meta:
        tag = 1
        max_args=2

class Is(GremlinQuery):
    pass
    class Meta:
        min_args = 1

class Has(GremlinQuery):
    pass
    class Meta:
        min_args = 2
        max_args = 2
        args_val = ((0,basestring),(1,basestring))

# Tagging
class Tag(GremlinQuery):
    pass
    class Meta:
        tag = 0
        min_args = 1
        max_args = 1
        args_val = (0,(Iterable,basestring))
        alias = ["As"]

class Save(GremlinQuery):
    pass
    class Meta:
        min_args = 2
        max_args = 2
        args_val = ((0,basestring),(1,basestring))
        tag = 1

class Back(GremlinQuery):
    pass
    class Meta:
        min_args = 1
        max_args = 1
        tag = 0

# Morphism
class Follow(GremlinQuery):
    pass
    class Meta:
        min_args = 1
        max_args = 1
        require_morphism = (0,)

class FollowR(GremlinQuery):
    pass
    class Meta:
        min_args = 1
        max_args = 1
        require_morphism = (0,)


# Joining
class Intersect(GremlinQuery):
    pass
    class Meta:
        alias = ["And"]
        min_args = 1
        max_args = 1
        args_val = (0,GremlinQuery)

class Union(GremlinQuery):
    pass
    class Meta:
        alias = ["Or"]
        min_args = 1
        max_args = 1
        args_val = (0,GremlinQuery)

# Terminal
class All(GremlinQuery):
    pass
    class Meta:
        max_args = 0
        terminal = True

class GetLimit(GremlinQuery):
    pass
    class Meta:
        min_args = 1
        max_args = 1
        terminal = True
        args_val = (0,int)

# Python Query
class Distinct(PythonQuery):
    _pyop = ['distinct']

class Filter(PythonQuery):
    def __init__(self,predecessor,f):
        super(Filter,self).__init__(predecessor)
        self._pyop = [lambda x:filter(f,x)]

class Map(PythonQuery):
    def __init__(self,predecessor,f):
        super(Map,self).__init__(predecessor)
        self._pyop = [lambda x:map(f,x)]