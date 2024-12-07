from flask import Flask, session
#from flask.ext.session import Session

SESSION_TYPE = 'memcache'

app = Flask(__name__)
#sess = Session()

from . import app

if __name__ == "__main__":
    # Quick test configuration. Please use proper Flask configuration options
    # in production settings, and use a separate file or environment variables
    # to manage the secret key!
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    #sess.init_app(app)

    app.debug = True
    app.run()
