from flask import Flask, jsonify, request, session, redirect, make_response
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

import store.config
import store.views
import store.s3

if __name__ == "__main__":
    app.run()


