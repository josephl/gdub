from flask import Flask, request, session, jsonify, render_template, g
from whisperctl import WhisperCtl
import graphyte
import metrics
import logging

app = Flask(__name__)
app.config.from_pyfile('config.py')
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
    session.update({ 'metrics': metrics.metrics() })
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def data():
    params = request.values.to_dict()
    if params.has_key('summarization'):
        summarization = int(params.pop('summarization'))
    else:
        summarization = session['graph'].step
    updateGraph(params)
    # BUG if timespan > 58hours, JSON req error. ?
    if summarization > session['graph'].step:
        table = session['graph'].timeTable(
            session['graph'].summarize(summarization))
    else:
        logger.info('step >= summary')
        table = session['graph'].timeTable()
    logger.info('table length: %d' %(len(table)))
    try:
        jsonData = jsonify(results=table)
    except:
        logger.error('data request jsonification')
    return jsonData

@app.route('/graphite/<path:metricPath>', methods=['GET'])
def graphite(metricPath):
    metricName = metricPath.rstrip('/').replace('/', '.')
    wc = WhisperCtl()
    metrics = wc.findall(metricName)
    if len(metrics) > 0:
        session.update({ 'metrics': metrics })
        return render_template('index.html')
    return str(metrics)

@app.route('/search', methods=['GET'])
def search():
    return None

def updateGraph(params):
    if session.has_key('graph'):
        if not session['graph'].has_key('target'):
            session.pop('graph')
        elif session['graph']['target'] != params['target']:
            session.pop('graph')
        else:
            # same metric, update instead of new request
            logger.info('same metric')
    # fresh request
    session.update({ 'graph': graphyte.Graphyte(params) })
    session['graph'].request()


if __name__ == '__main__':
    app.run(host='0.0.0.0')
