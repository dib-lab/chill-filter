# /path-to-your-project/gunicorn_conf.py
bind = '0.0.0.0:5000'
worker_class = 'sync'
loglevel = 'debug'
accesslog = 'logs/access_log'
acceslogformat ="%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
errorlog =  'logs/error_log'
