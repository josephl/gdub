from flask import Flask, request, session, jsonify, render_template, g, \
    redirect, current_app
import whisperctl
import graphyte
import logging
from sys import argv
import json
from functools import wraps
 
app = Flask(__name__)
app.config.from_pyfile(argv[1])
app.secret_key = 'IDEALIST'
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.route('/data', methods=['GET'])
@support_jsonp
def data():
    #params = request.values.to_dict()
    params = parseRequest()
    host = app.config['GRAPHITE_HOST']
    sslcert = app.config['SSL_CERT']

    if not host.endswith('/render'):
        host = host.rstrip('/') + '/render'

    logger.info(host)
    logger.info(params)

    graphiteDataframe = graphyte.request(host, sslcert, **params)
    dataset, stats = graphyte.plotData(graphiteDataframe, 'ffill', True)

    return jsonify(results=dataset, stats=stats)

@app.route('/menu', methods=['GET'])
@support_jsonp
def menu():
    """Obtain metric names from Graphite"""
    graphiteIndex = whisperctl.index()
    return jsonify(graphiteIndex.dictify())

def parseRequest():
    params = request.values.to_dict()
    if 'target[]' in params:
        params.pop('target[]')
        params.update({ 'target': request.values.getlist('target[]') })
    return params


def updateGraph(params):
    if hasattr(g, 'graph') and g.graph is not None:
        if not g.graph.has_key('target'):
            g.graph = None
        elif g.graph['target'] != params['target']:
            g.graph = None
        else:
            # same metric, update instead of new request
            logger.info('same metric')
    # fresh request
    setattr(g, 'graph', graphyte.request(params))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
