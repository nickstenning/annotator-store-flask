from annotator.model import Annotation, Range
from annotator.model import create_all, drop_all, session

class TestAnnotation():
    def setup(self):
        create_all()

    def teardown(self):
        session.remove()
        drop_all()

    def test_id(self):
        ann = Annotation()
        session.commit()
        assert isinstance(ann.id, int), "annotation id wasn't an integer"

    def test_text(self):
        ann = Annotation(text="Hello there")
        assert ann.text == "Hello there", "annotation text wasn't set"

    def test_ranges(self):
        ann = Annotation()
        ann.ranges.append(Range())
        ann.ranges.append(Range())
        assert len(ann.ranges) == 2, "ranges weren't added to annotation"

    def test_to_dict(self):
        ann = Annotation(text="Foo")
        data = {'ranges': [], 'text': 'Foo', 'id': None}
        assert ann.to_dict() == data, "annotation wasn't converted to dict correctly"

    def test_to_dict_with_range(self):
        ann = Annotation(text="Bar")
        ann.ranges.append(Range())
        assert len(ann.to_dict()['ranges']) == 1, "annotation ranges weren't in dict"

    def test_from_dict(self):
        ann = Annotation()
        ann.from_dict({'text': 'Baz'})
        assert ann.text == "Baz", "annotation wasn't updated from dict"

    def test_from_dict_with_range(self):
        ann = Annotation()
        ann.from_dict({'ranges': [{}]})
        assert len(ann.ranges) == 1, "annotation ranges weren't updated from dict"

    def test_extras_in(self):
        ann = Annotation()
        ann.from_dict({'foo':1, 'bar':2})
        print ann.extras
        assert ann.extras == '{"foo": 1, "bar": 2}', "extras weren't serialized properly"

    def test_extras_out(self):
        ann = Annotation(extras='{"bar": 3, "baz": 4}')
        data = ann.to_dict()
        assert data['bar'] == 3, "extras weren't deserialized properly"
        assert data['baz'] == 4, "extras weren't deserialized properly"

    def test_repr(self):
        ann = Annotation(text="FooBarBaz")
        assert ann.__repr__() == '<Annotation None "FooBarBaz">', "annotation repr incorrect"

class TestRange():
    def setup(self):
        create_all()

    def teardown(self):
        session.remove()
        drop_all()

    def test_id(self):
        rng = Range()
        session.commit()
        assert isinstance(rng.id, int), "range id wasn't an integer"

    def test_start(self):
        rng = Range(start='/div', startOffset=123)
        assert rng.start == '/div', "range start wasn't set correctly"
        assert rng.startOffset == 123, "range startOffset wasn't set correctly"

    def test_end(self):
        rng = Range(end='/footer', endOffset=987)
        assert rng.end == '/footer', "range start wasn't set correctly"
        assert rng.endOffset == 987, "range startOffset wasn't set correctly"

    def test_to_dict(self):
        rng = Range(start='/div', startOffset=123, end='/footer', endOffset=987)
        data = {'id': None, 'start': '/div', 'startOffset': 123, 'end': '/footer', 'endOffset': 987}
        result = rng.to_dict()
        assert result['start'] == data['start'], "range start wasn't in dict"
        assert result['startOffset'] == data['startOffset'], "range startOffset wasn't in dict"
        assert result['end'] == data['end'], "range end wasn't in dict"
        assert result['endOffset'] == data['endOffset'], "range endOffset wasn't in dict"

    def test_repr(self):
        rng = Range(start='/p', startOffset=123, end='/div', endOffset=456)
        assert rng.__repr__() == '<Range None /p@123 /div@456>', "range repr incorrect"
