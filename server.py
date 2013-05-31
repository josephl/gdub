from flask import Flask, request, session, jsonify, render_template, g, \
    redirect, current_app
from ssl import SSLError
import whisperctl
import graphyte
import graphalytics
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

    # if analytics metrics exist, resampleFreq must be set
    if (len(filter(lambda x: x.startswith('ga:'), params.get('target'))) > 0
            and 'resampleFreq' not in params):
        params.update({ 'resampleFreq': 'H' })

    graphiteParams = {}
    graphiteParams.update(params)
    graphiteParams.update({ 'target': filter(
            lambda x: not x.startswith('ga:'), params.get('target')) })
    graphiteDataframe = None
    if graphiteParams.get('target'):
        graphiteDataframe = graphyte.request(host, sslcert, **graphiteParams)

    # Assumes there MUST be a graphite metric for analytics metrics
    analyticsParams = analyticsOptions(params, graphiteDataframe)
    analyticsDataframe = None
    if analyticsParams is not None:
        if graphiteDataframe is not None:
            try:
                analyticsData = graphalytics.request(**analyticsParams)
                analyticsDataframe = graphyte.getDataframe(analyticsData)
            except SSLError as se:
                print 'SSL error: %s' % se
            graphiteDataframe = graphyte.mergeAnalytics(graphiteDataframe,
                                                        analyticsDataframe)

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

def analyticsOptions(params, graphiteDF=None):
    if graphiteDF is not None:
        graphiteIndex = graphiteDF.index
        filteredIndex = graphiteDF.dropna().index
        #import pdb; pdb.set_trace()
        start = filteredIndex[0].to_datetime().strftime('%s')
        end = filteredIndex[-1].to_datetime().strftime('%s')
    else:
        start = None
        end = None
    metrics = filter(lambda x: x.startswith('ga:'), params.get('target'))
    if len(metrics) == 0:
        return None
    query = {
            'metrics': metrics,
            'dimensions' : ['ga:date',]
            }
    if 'resampleFreq' not in params or params.get('resampleFreq') != 'D':
        query['dimensions'] += ['ga:hour', ]

    if 'from' in params and int(params.get('from')) != 0:
        query.update({'start_date': params.get('from')})
    elif graphiteIndex is not None:
        query.update({ 'start_date': start })

    if 'until' in params is not None:
        query.update({ 'end_date': params.get('until') })
    elif graphiteIndex is not None:
        query.update({ 'end_date': end })
        
    ga_options = {
        'webProperty': app.config['GA_WEB_PROPERTY'],
        'profile': app.config['GA_PROFILE'],
        'config': [
            app.config['GA_TOKEN_FILE_NAME'],
            app.config['GA_CLIENT_SECRETS']
            ],
        'query': query
        }
    return ga_options

if __name__ == '__main__':
    app.run(host='0.0.0.0')
