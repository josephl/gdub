from flask import Flask, request, session, jsonify, render_template, g
import whisperctl
import graphyte
import metrics
import logging
from sys import argv

app = Flask(__name__)
app.config.from_pyfile(argv[1])
app.secret_key = 'IDEALIST'
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def getParams():
    d = {}
    for key, val in request.values.items():
        d.update({ key: val })
    return d

@app.route('/graphite/', methods=['GET'])
def index():
    g.update({ 'metrics': metrics.metrics() })
    return render_template('index.html')

@app.route('/data', methods=['GET'])
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
def metrics():
    params = request.values.to_dict()
    

@app.route('/graphite/<path:metricPath>', methods=['GET'])
def graphite(metricPath):
    metricName = metricPath.rstrip('/').replace('/', '.')
    wc = WhisperCtl()
    metrics = wc.findall(metricName)
    if len(metrics) > 0:
        g.metrics = metrics
        return render_template('index.html')
    return str(metrics)

@app.route('/search', methods=['GET'])
def search():
    """Obtain metrics from Graphite"""
    return None

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
