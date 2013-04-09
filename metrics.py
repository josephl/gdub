def metrics():
    metricPath = '/opt/graphite/storage/index'
    with open(metricPath, 'r') as mf:
        metricls = mf.read().strip().split('\n')
    return metricls
