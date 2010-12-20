from flask import json, url_for

from annotator.store import app, setup_app
from annotator.model import Annotation, Range
from annotator.model import create_all, drop_all, session

def setup():
    app.config['MOUNTPOINT'] = ''
    setup_app()

class TestStore():
    def setup(self):
        app.config['AUTH_ON'] = False
        self.app = app.test_client()
        create_all()

    def teardown(self):
        session.remove()
        drop_all()

    def test_index(self):
        assert self.app.get('/annotations').data == "[]", "response should be empty list"

    def test_create(self):
        import re
        payload = json.dumps({'name': 'Foo'})
        response = self.app.post('/annotations', data=payload, content_type='application/json')

        # See http://bit.ly/gxJBHo for details of this change.
        # assert response.status_code == 303, "response should be 303 SEE OTHER"
        # assert re.match(r"http://localhost/store/\d+", response.headers['Location']), "response should redirect to read_annotation url"

        assert response.status_code == 200, "response should be 200 OK"
        data = json.loads(response.data)
        assert 'id' in data, "annotation id should be returned in response"

    def test_read(self):
        Annotation(text=u"Foo", id=123)
        session.commit()
        response = self.app.get('/annotations/123')
        data = json.loads(response.data)
        assert data['id'] == 123, "annotation id should be returned in response"
        assert data['text'] == "Foo", "annotation text should be returned in response"

    def test_read_notfound(self):
        response = self.app.get('/annotations/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_update(self):
        ann = Annotation(text=u"Foo", id=123)
        session.commit() # commits expire all properties of `ann'

        payload = json.dumps({'id': 123, 'text': 'Bar'})
        response = self.app.put('/annotations/123', data=payload, content_type='application/json')

        assert ann.text == "Bar", "annotation wasn't updated in db"

        data = json.loads(response.data)
        assert data['text'] == "Bar", "update annotation should be returned in response"

    def test_update_notfound(self):
        response = self.app.put('/annotations/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_delete(self):
        ann = Annotation(text=u"Bar", id=456)
        session.commit()

        response = self.app.delete('/annotations/456')
        assert response.status_code == 204, "response should be 204 NO CONTENT"

        assert Annotation.get(456) == None, "annotation wasn't deleted in db"

    def test_delete_notfound(self):
        response = self.app.delete('/annotations/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_cors_preflight(self):
        response = self.app.open('/annotations', method="OPTIONS")

        headers = dict(response.headers)

        assert headers['Access-Control-Allow-Methods'] == 'GET, POST, PUT, DELETE', \
            "Did not send the right Access-Control-Allow-Methods header."

        assert headers['Access-Control-Allow-Origin'] == '*', \
            "Did not send the right Access-Control-Allow-Origin header."

        assert headers['Access-Control-Expose-Headers'] == 'Location', \
                "Did not send the right Access-Control-Expose-Headers header."

class TestStoreAuth():
    def setup(self):
        app.config['AUTH_ON'] = True
        self.app = app.test_client()
        create_all()

    def teardown(self):
        session.remove()
        drop_all()

    def test_reject_bare_request(self):
        response = self.app.get('/annotations')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"
