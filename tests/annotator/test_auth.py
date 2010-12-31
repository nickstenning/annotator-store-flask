import hashlib
import datetime

from werkzeug import Headers

import annotator.model as model
import annotator.auth as auth

class MockRequest():
    def __init__(self, headers):
        self.headers = headers

def iso8601(t):
    t = datetime.datetime.now() if t == 'now' else t
    return t.strftime("%Y-%m-%dT%H:%M:%S")

def make_token(consumerKey, userId, issueTime):
    c = model.Consumer.get(consumerKey)
    return hashlib.sha256(c.secret + userId + issueTime).hexdigest()

def make_request(consumerKey, userId, issueTime):
    return MockRequest(Headers([
        ('x-annotator-consumer-key', consumerKey),
        ('x-annotator-auth-token', make_token(consumerKey, userId, issueTime)),
        ('x-annotator-auth-token-issue-time', issueTime),
        ('x-annotator-user-id', userId)
    ]))

def setup():
    c = model.Consumer(key='testConsumer', secret='testConsumerSecret', ttl=300)
    model.session.commit()

class TestAuth():
    def test_verify_token(self):
        issueTime = iso8601('now')
        tok = make_token('testConsumer', 'alice', issueTime)
        assert auth.verify_token(tok, 'testConsumer', 'alice', issueTime), "token should have been verified"

    def test_reject_inauthentic_token(self):
        issueTime = iso8601('now')
        tok = make_token('testConsumer', 'alice', issueTime)
        assert not auth.verify_token(tok, 'testConsumer', 'bob', issueTime), "token was inauthentic, should have been rejected"

    def test_reject_expired_token(self):
        issueTime = iso8601(datetime.datetime.now() - datetime.timedelta(seconds=301))
        tok = make_token('testConsumer', 'alice', issueTime)
        assert not auth.verify_token(tok, 'testConsumer', 'bob', issueTime), "token had expired, should have been rejected"

    def test_verify_request(self):
        issueTime = iso8601('now')
        request = make_request('testConsumer', 'alice', issueTime)
        assert auth.verify_request(request), "request should have been verified"

    def test_reject_request_missing_headers(self):
        issueTime = iso8601('now')
        request = make_request('testConsumer', 'alice', issueTime)
        del request.headers['x-annotator-consumer-key']
        assert not auth.verify_request(request), "request missing consumerKey should have been rejected"

    def test_verify_request_mixedcase_headers(self):
        issueTime = iso8601('now')
        request = make_request('testConsumer', 'alice', issueTime)
        request.headers['X-Annotator-Consumer-Key'] = request.headers['x-annotator-consumer-key']
        assert auth.verify_request(request), "request with mixed-case headers should have been verified"

    def test_get_request_userid(self):
        issueTime = iso8601('now')
        request = make_request('testConsumer', 'bob', issueTime)
        assert auth.get_request_userid(request) == 'bob', "didn't extract userid from headers"
