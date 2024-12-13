from flask import Flask, session
import argparse

# from flask.ext.session import Session

SESSION_TYPE = "memcache"

app = Flask(__name__)
# sess = Session()

from . import app

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--port", default=5000, type=int)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args()
    # Quick test configuration. Please use proper Flask configuration options
    # in production settings, and use a separate file or environment variables
    # to manage the secret key!
    app.secret_key = "super secret key"
    app.config["SESSION_TYPE"] = "filesystem"

    # sess.init_app(app)

    app.debug = True
    app.run(port=args.port, host=args.host)
