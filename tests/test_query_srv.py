from __future__ import absolute_import
import unittest, responses, json
from cayley import g

class TestQuerySrv(unittest.TestCase):
    __DATA ={
        'g.Vertex("\\"Paul McCartney\\"@en").All()':
            '{"result": [{"id": "\\"Paul McCartney\\"@en"}]}',
        'g.Vertex("\\"Paul McCartney\\"@en").In("http://rdf.freebase.com/ns/type.object.name").All()':
            '{"result": [{"id": "http://rdf.freebase.com/ns/m.03j24kf"}]}',
        'g.Vertex("\\"Paul McCartney\\"@en").Out("http://rdf.freebase.com/ns/common.topic.alias").All()':
            '{"result": null}',
        'g.Vertex("\\"Paul McCartney\\"@en").In("http://rdf.freebase.com/ns/type.\
object.name").Out("http://rdf.freebase.com/ns/common.topic.alias").All()':
            '{"result": [{"id": "\\"Paul McCartney\'s musical career\\"@en"},{"id":\
"\\"Sir James Paul McCartney, MBE\\"@en"},{"id": "\\"Bernard Webb\\"@en"},{"id": "\\"Wings\\"@en"},\
{"id": "\\"Sir Paul McCartney\\"@en"},{"id": "\\"Macca\\"@en"}, {"id": "\\"James Paul McCartney\\"@en"\
}, {"id": "\\"The Beatles\\"@en"}, {"id": "\\"Paul\\"@en"}, {"id": "\\"Sir James Paul McCartney\\"@en"\
}, {"id": "\\"Percy Thrillington\\"@en"}, {"id": "\\"Solo career of Paul McCartney\\"@en"}, {"id":\
"\\"Percy \\\\\\"Thrills\\\\\\" Thrillington\\"@en"}, {"id": "\\"Thrillington, Percy \'Thrills\'\\"@en"\
}]}',
        'g.Vertex("\\"Paul McCartney\\"@en").In("http://rdf.freebase.com/ns/type.object.name")\
.Tag("free_id").All()':
            '{"result": [{"free_id": "http://rdf.freebase.com/ns/m.03j24kf","id":\
"http://rdf.freebase.com/ns/m.03j24kf"}]}',
    }

    def responses_callback(self, request):
        query = request.body
        try:
            data = self.__DATA[query]
            return (200, {},data)
        except KeyError:
            return (404,)

    @responses.activate
    def test_base_query_str(self):
        responses.add_callback(responses.POST,"http://localhost:64210/api/v1/query/gremlin",
            callback = self.responses_callback)
        x = g.V('"Paul McCartney"@en').All()
        self.assertEqual(x[0].id, '"Paul McCartney"@en')

    @responses.activate
    def test_in_query_str(self):
        responses.add_callback(responses.POST,"http://localhost:64210/api/v1/query/gremlin",
            callback = self.responses_callback)
        x = g.V('"Paul McCartney"@en').In("http://rdf.freebase.com/ns/type.object.name").All()
        self.assertEqual(x[0].id, 'http://rdf.freebase.com/ns/m.03j24kf')

    @responses.activate
    def test_out_query_str(self):
        responses.add_callback(responses.POST,"http://localhost:64210/api/v1/query/gremlin",
            callback = self.responses_callback)
        x = g.V('"Paul McCartney"@en').Out("http://rdf.freebase.com/ns/common.topic.alias").All()
        self.assertEqual(len(x),0)

    @responses.activate
    def test_inout_query_str(self):
        responses.add_callback(responses.POST,"http://localhost:64210/api/v1/query/gremlin",
            callback = self.responses_callback)
        x = g.V('"Paul McCartney"@en').In("http://rdf.freebase.com/ns/type.object.name").\
            Out("http://rdf.freebase.com/ns/common.topic.alias").All()
        self.assertEqual(len(x),14)
        data = [u'"Paul McCartney\'s musical career"@en',
            u'"Sir James Paul McCartney, MBE"@en',
            u'"Bernard Webb"@en',
            u'"Wings"@en',
            u'"Sir Paul McCartney"@en',
            u'"Macca"@en',
            u'"James Paul McCartney"@en',
            u'"The Beatles"@en',
            u'"Paul"@en',
            u'"Sir James Paul McCartney"@en',
            u'"Percy Thrillington"@en',
            u'"Solo career of Paul McCartney"@en',
            u'"Percy \\"Thrills\\" Thrillington"@en',
            u'"Thrillington, Percy \'Thrills\'"@en'
            ]
        for pos,res in enumerate(data):
            self.assertEqual(x[pos].id,res)

    @responses.activate
    def test_tag_query_str(self):
        responses.add_callback(responses.POST,"http://localhost:64210/api/v1/query/gremlin",
            callback = self.responses_callback)
        x = g.V('"Paul McCartney"@en').In("http://rdf.freebase.com/ns/type.object.name").\
            Tag("free_id").All()
        self.assertEqual(x[0].id, 'http://rdf.freebase.com/ns/m.03j24kf')
        self.assertEqual(x[0].free_id, 'http://rdf.freebase.com/ns/m.03j24kf')
        self.assertEqual(len(x), 1)