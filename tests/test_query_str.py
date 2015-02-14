import unittest
from cayley import g

class TestQueryStr(unittest.TestCase):
    def test_base_query_str(self):
        x = g.V('"Paul McCartney"@en').All()
        self.assertEqual(x._make_query(), 'g.Vertex("\\"Paul McCartney\\"@en").All()')

    def test_in_query_str(self):
        x = g.V('"Paul McCartney"@en').In("http://rdf.freebase.com/ns/type.object.name").All()
        self.assertEqual(x._make_query(),
            'g.Vertex("\\"Paul McCartney\\"@en").In("http://rdf.freebase.com/ns/type.\
object.name").All()')

    def test_out_query_str(self):
        x = g.V('"Paul McCartney"@en').Out("http://rdf.freebase.com/ns/common.topic.alias").All()
        self.assertEqual(x._make_query(),
            'g.Vertex("\\"Paul McCartney\\"@en").Out("http://rdf.freebase.com/ns/common.\
topic.alias").All()')

    def test_inout_query_str(self):
        x = g.V('"Paul McCartney"@en').In("http://rdf.freebase.com/ns/type.object.name").\
            Out("http://rdf.freebase.com/ns/common.topic.alias").All()
        self.assertEqual(x._make_query(),
            'g.Vertex("\\"Paul McCartney\\"@en").In("http://rdf.freebase.com/ns/type.\
object.name").Out("http://rdf.freebase.com/ns/common.topic.alias").All()')

    def test_tag_query_str(self):
        x = g.V('"Paul McCartney"@en').In("http://rdf.freebase.com/ns/type.object.name").\
            Tag("free_id").All()
        self.assertEqual(x._make_query(),
            'g.Vertex("\\"Paul McCartney\\"@en").In("http://rdf.freebase.com/ns/type.\
object.name").Tag("free_id").All()')