from store import app, db

from flask import Flask, jsonify, request, session, redirect, make_response
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func


def auth():
  if 'admin' in session and session['admin']:
    return True
  else: 
    return False

