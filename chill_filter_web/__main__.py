from flask import Flask, session
import argparse

# from flask.ext.session import Session

SESSION_TYPE = "memcache"

if __name__ == "__main__":
    from . import create_app

    p = argparse.ArgumentParser()
    p.add_argument("-p", "--port", default=5000, type=int)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args()
    app = create_app()
    app.run(port=args.port, host=args.host)
