from flask import Flask, Module
from flask import abort, json, redirect, request, url_for

from .model import Annotation, Range, session
from . import auth

__all__ = ["app", "store", "setup_app"]

app = Flask('annotator')
store = Module(__name__)

def setup_app():
    app.register_module(store, url_prefix=app.config['MOUNTPOINT'])

# We define our own jsonify rather than using flask.jsonify because we wish
# to jsonify arbitrary objects (e.g. index returns a list) rather than kwargs.
def jsonify(obj, *args, **kwargs):
    res = json.dumps(obj, indent=None if request.is_xhr else 2)
    return app.response_class(res, mimetype='application/json', *args, **kwargs)

def unjsonify(str):
    return json.loads(str)

def get_current_userid():
    return auth.get_request_userid(request)

@store.before_request
def before_request():
    if app.config['AUTH_ON'] and not auth.verify_request(request):
        return jsonify("Cannot authorise request. Perhaps you didn't send the x-annotator headers?", status=401)

@store.after_request
def after_request(response):
    if response.status_code < 300:
        response.headers['Access-Control-Allow-Origin']   = '*'
        response.headers['Access-Control-Expose-Headers'] = 'Location'
        response.headers['Access-Control-Allow-Methods']  = 'GET, POST, PUT, DELETE'
        response.headers['Access-Control-Max-Age']        = '86400'

    return response

# INDEX
@store.route('/annotations')
def index():
    annotations = [a.to_dict() for a in Annotation.query.all() if a.authorise('read', get_current_userid())]
    return jsonify(annotations)

# CREATE
@store.route('/annotations', methods=['POST'])
def create_annotation():
    if request.json:
        annotation = Annotation()
        annotation.from_dict(request.json)
        session.commit()

        return jsonify(annotation.to_dict())
    else:
        return jsonify('No parameters given. Annotation not created.', status=400)

# READ
@store.route('/annotations/<int:id>')
def read_annotation(id):
    annotation = Annotation.get(id)

    if not annotation:
        return jsonify('Annotation not found.', status=404)

    elif annotation.authorise('read', get_current_userid()):
        return jsonify(annotation.to_dict())

    else:
        return jsonify('Could not authorise request. No update performed', status=401)

# UPDATE
@store.route('/annotations/<int:id>', methods=['PUT'])
def update_annotation(id):
    annotation = Annotation.get(id)

    if not annotation:
        return jsonify('Annotation not found. No update performed.', status=404)

    elif request.json and annotation.authorise('update', get_current_userid()):
        annotation.from_dict(request.json)
        session.commit()
        return jsonify(annotation.to_dict())

    else:
        return jsonify('Could not authorise request. No update performed', status=401)

# DELETE
@store.route('/annotations/<int:id>', methods=['DELETE'])
def delete_annotation(id):
    annotation = Annotation.get(id)

    if not annotation:
        return jsonify('Annotation not found. No delete performed.', status=404)

    elif annotation.authorise('delete', get_current_userid()):
        annotation.delete()
        session.commit()
        return None, 204

    else:
        return jsonify('Could not authorise request. No update performed', status=401)

# Search
@store.route('/search')
def search_annotations():
    params = [
        (k,v) for k,v in request.args.items() if k not in [ 'all_fields', 'offset', 'limit' ]
    ]
    all_fields = request.args.get('all_fields', False)
    all_fields = bool(all_fields)
    offset = request.args.get('offset', 0)
    limit = int(request.args.get('limit', 100))
    if limit < 0:
        limit = None

    q = Annotation.query
    for k,v in params:
        kwargs = { k: unicode(v) }
        q = q.filter_by(**kwargs)

    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    if all_fields:
        rows = [ x.to_dict() for x in rows ]
    else:
        rows = [ {'id': x.id} for x in rows ]

    qrows = {
        'total': total,
        'rows': rows
    }
    return jsonify(qrows)

