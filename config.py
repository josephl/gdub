# gdub default configs
DEFAULT_OPTIONS = {
    'from' : '-1d',
    'format': 'pickle'
}
GRAPHITE_HOST = 'https://graphite.dev.awbdev.org'
SSL_CERT = '/opt/graphite/idealist.pem'

# Google Analytics default configs
GA_TOKEN_FILE_NAME = '/opt/graphite/analytics.dat'
GA_CLIENT_SECRETS = '/opt/graphite/client_secrets.json'
GA_WEB_PROPERTY = {'name': 'http://idealist.org'}
GA_PROFILE = {'name': 'i3: English w/o filter'}
