from flask import Flask, request, session, jsonify, render_template, g, \
    redirect, current_app
import whisperctl
import graphyte
import metrics
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

def getParams():
    d = {}
    for key, val in request.values.items():
        d.update({ key: val })
    return d

@app.route('/graphite/', methods=['GET'])
@support_jsonp
def index():
    g.update({ 'metrics': metrics.metrics() })
    return render_template('index.html')

@app.route('/data', methods=['GET'])
@support_jsonp
def data():
    """Request metric data."""
    params = request.values.to_dict()
    if params.has_key('summarization'):
        summarization = int(params.pop('summarization'))
    else:
        summarization = g.graph.step
    updateGraph(params)
    # BUG if timespan > 58hours, JSON req error. ?
    if summarization > g.graph.step:
        table = g.graph.timeTable(
            g.graph.summarize(summarization))
    elif summarization == g.graph.step:
        logger.info('step == summary')
        table = g.graph.timeTable(
            g.graph.summarize(summarization))
    else:
        logger.info('step >= summary')
        table = g.graph.timeTable()
    logger.info('table length: %d' %(len(table)))
    try:
        jsonData = jsonify(results=table)
    except:
        logger.error('data request jsonification')
    return jsonData

@app.route('/metrics', methods=['GET'])
@support_jsonp
def metrics():
    params = request.values.to_dict()
    

@app.route('/graphite/<path:metricPath>', methods=['GET'])
@support_jsonp
def graphite(metricPath):
    metricName = metricPath.rstrip('/').replace('/', '.')
    wc = WhisperCtl()
    metrics = wc.findall(metricName)
    if len(metrics) > 0:
        g.metrics = metrics
        return render_template('index.html')
    return str(metrics)

@app.route('/menu', methods=['GET'])
@support_jsonp
def menu():
    """Obtain metric names from Graphite"""
    graphiteIndex = whisperctl.index()
    return jsonify(graphiteIndex.dictify())

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
