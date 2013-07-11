import stripe
import datetime

from store import app, db, s3

from flask import Flask, jsonify, request, session, redirect, make_response, url_for
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), unique=False)
  email = db.Column(db.String(255), unique=True)
  password = db.Column(db.String(255), unique=False)
  
  def __init__(self, name, email, password):
    self.name = name
    self.email = email
    self.password = generate_password_hash(password)

class Ip(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  ipaddr = db.Column(db.String(255), unique=False)
  userid = db.Column(db.Integer)
  visitat = db.Column(db.DateTime)

  def __init__(self, ipaddr, userid):
    self.ipaddr = ipaddr
    self.userid = userid
    self.visitat = datetime.datetime.now()

class Code(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  code = db.Column(db.String(255), unique=False)
  credit = db.Column(db.Integer)
  conf = db.Column(db.Integer)
  userid = db.Column(db.Integer)

class History(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  type = db.Column(db.String(255))
  purchase = db.Column(db.Integer)
  point = db.Column(db.Integer)
  userid = db.Column(db.Integer)
  detail = db.Column(db.Text)
  recordingid = db.Column(db.Integer)
  created = db.Column(db.DateTime)
  def __init__(self, type, purchase, point, userid, detail, recordingid):
    self.type = type
    self.purchase = purchase
    self.point = point
    self.userid = userid
    self.detail = detail
    self.recordingid = recordingid
    self.created = datetime.datetime.now()

class Recording(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  bucket = db.Column(db.String(255), unique=False)
  filename = db.Column(db.String(255), unique=True)
  title = db.Column(db.Text, unique=True)
  speaker = db.Column(db.String(255), unique=False)
  conf = db.Column(db.Integer)
  year = db.Column(db.Integer)
  ppt = db.Column(db.String(255))
  note = db.Column(db.String(255))
  description = db.Column(db.Text)
  categoryid = db.Column(db.Integer, db.ForeignKey('category.id'))

  def __init__(self, bucket, filename, title, speaker, conf, ppt, recordtype, description, note, year):
    self.bucket = bucket
    self.filename = filename
    self.title = title
    self.speaker = speaker
    self.conf = conf
    self.ppt = ppt
    self.note = note
    self.description = description
    self.categoryid = recordtype
    self.year = year

class Category(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String(255), unique=True)
  recording = db.relationship('Recording', backref='category')

def isios(req):
  # if from ios, do not trigger download but stream the files instead. 
  if ('iPad' in req.user_agent.string) or ('iPhone' in req.user_agent.string):
    return True
  return False

def makeconf(conf):
  conference = {}
  if conf == 'chicago':
    conference['name'] = 'Chicago'
    conference['code'] = 0
    conference['path'] = 'chicago'
    conference['bucket'] = '2012-chicago'
  else:
    conference['name'] = 'Indianapolis'
    conference['code'] = 1
    conference['path'] = 'indy'
    conference['bucket'] = '2012-indy'

  return conference

def auth():
  if 'user' in session and not session['user'] is None:
    return True
  else: 
    return False


def authadmin():
  if 'admin' in session and session['admin']:
    return True
  else:
    return False

@app.route("/store/admin")
def admin():
  if not authadmin():
    return redirect("/store/admin/login")
  
  if not 'conf' in session:
    session['conf'] = 0

  conf = session['conf']
  recordings = Recording.query \
    .filter_by(conf=conf) \
    .order_by(Recording.id)

  return render_template("admin/main.html", conf=conf, recordings=recordings)

@app.route("/store/admin/update/<id>", methods=['POST'])
def update(id):
  if not authadmin():
    return redirect("/store/admin/login")

  targetid = int(id)
  recording = Recording.query.filter_by(id=targetid).first()

  if recording is None:
    return redirect("/store/admin")

  title = request.form['title']
  ppt = request.form['ppt']
  note = request.form['note']
  filename = request.form['filename']
  description = request.form['description']

  recording.title = title
  recording.ppt = ppt
  recording.note = note
  recording.filename = filename
  recording.description = description

  db.session.add(recording)
  db.session.commit()

  return redirect("/store/admin")  

@app.route("/store/admin/remove", methods=["POST"])
def remove_recording():
  if not authadmin():
    return redirect("/store/admin/login")

  id = int(request.form['id'])
  recording = Recording.query.filter_by(id=id).first()
  if not recording is None:
    db.session.delete(recording)
    db.session.commit()

  return redirect("/store/admin")

@app.route("/store/admin/add", methods=["POST"])
def add_recording():
  if not authadmin():
    return redirect("/store/admin/login")

  recordtype = request.form['type']    
  title = request.form['title']
  speaker = request.form['speaker']
  filename = request.form['file']
  ppt = request.form['ppt']
  note = request.form['note']
  desc = request.form['desc']
  conf = int(request.form['conf'])
  description = request.form['desc']
  year = app.config['YEAR']

  bucket = str(year) + '-chicago'
  if conf == 1:
    bucket = str(year) + '-indy'

  recording = Recording(bucket, filename, title, speaker, conf, ppt, recordtype, description, note, year)
  db.session.add(recording)
  db.session.commit()

  return redirect("/store/admin")


@app.route("/store/admin/choose/<conf>")
def choose(conf):
  session['conf'] = int(conf)
  return redirect("/store/admin")

@app.route("/store/admin/login", methods=["GET", "POST"])
def adminlogin():
  if request.method == "GET":
    return render_template("admin/login.html", autherror=False)

  user = request.form["user"]
  passwd = request.form["pass"]

  if user == "store" and passwd == "gkskslaskfk":
    session['admin'] = True
    return redirect("/store/admin")

  return render_template("admin/login.html", autherror=True)

@app.route("/store/newmember", methods=['GET', 'POST'])
def newmember():
  if request.method == 'GET':
    return render_template('newmember.html')
  else:
    email = request.form['email']
    name = request.form['name']
    password = request.form['pass']

    user = User.query.filter_by(email=email).first()
    if not user is None:
      return render_template('newmember.html', 
        error=True, reason='exists', email=email)

    user = User(name, email, password)

    db.session.add(user)
    db.session.commit()

    session['user'] = user
    return render_template('newmember.html', user=user, done=True)

@app.route("/store/checkout/<points>")
def checkout(points):
  return render_template('checkout.html', amount=points)

@app.route("/store/swipe", methods=['POST'])
def swipe():
  amount = int(request.form['amount'])

  if not auth():
    return render_template('login.html')

  stripe.api_key = app.config['STRIPE_API_KEY']
  token = request.form['stripeToken']
  description = "KOSTA/USA Store - " + request.form['name']

  try:
    charge = stripe.Charge.create(
      amount=amount,
      currency="usd",
      card=token,
      description=description
    )
  except stripe.CardError, e:
    return render_template('swipe.html', result=False)

  usd = charge.amount / 100
  ts = datetime.datetime.fromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M:%S')

  user = session['user']
    
  history = History('credit', 1, usd, user.id, charge.id, 0)
  db.session.add(history)
  db.session.commit()

  return render_template('swipe.html', amount=usd, ts=ts, id=charge.id, charge=charge, result=True)

@app.route("/store/logout")
def logout():
  del session['user'] 
  return redirect('/store') 

@app.route("/store/login", methods=['POST'])
def login():

  email = request.form['email']
  password = request.form['pass']

  user = User.query \
    .filter_by(email=email).first()

  if user is None:
    return render_template('login.html', error=True, reason='auth')

  if not check_password_hash(user.password, password):
    return render_template('login.html', error=True, reason='auth')

  locations = Ip.query.filter_by(userid=user.id).count()
  if locations > 10:
    return render_template('login.html', error=True, reason='toomany')

  session['user'] = user

  ipaddr = request.remote_addr
  userid = user.id

  checkip = Ip.query \
    .filter_by(ipaddr=ipaddr) \
    .filter_by(userid=userid) \
    .first()

  if checkip is None:
    ip = Ip(ipaddr, userid)
    
    db.session.add(ip)
    db.session.flush()

  return redirect(url_for('main'))

@app.route("/store/download/<material>/<id>")
def url(material,id):
  if not auth():
    return render_template('login.html')

  user = session['user']
  logs = get_logs(user)
  credit = get_credit(logs)

  targetid = int(id)

  recording = Recording.query.filter_by(id=targetid).first()
  if recording is None:
    return jsonify(result=False)

  if not credit['unlimited'] and not recording.categoryid == 6:
    instance = History.query \
      .filter_by(userid=user.id) \
      .filter_by(recordingid=targetid) \
      .first()

    if instance is None:
      return jsonify(result=False)

  resource = recording.filename
  if material == 'slide' and recording.ppt != '':
    resource = recording.ppt

  elif material == 'note' and recording.note != '':
    resource = recording.note

  if isios(request):
    resource = 'mobile/' + resource

  url = s3.url(recording.bucket, resource, 60*5)
  return jsonify(
    result=True,
    url=url
  )

@app.route("/store")
def main():
  if not auth():
    return render_template('login.html')

  user = session['user']
  logs = get_logs(user)
  credit = get_credit(logs)


  allrecordings = Recording.query.order_by(Recording.conf).order_by(Recording.categoryid).all()

  inventory = {
    'chicago' : {},
    'indianapolis' : {}
  }

  for recording in allrecordings:
    conf = 'chicago'
    if recording.conf == 1:
      conf = 'indianapolis'

    year = recording.year
    if not year in inventory[conf]:
      inventory[conf][year] = {}

    category = recording.categoryid
    if not category in inventory[conf][year]:
      inventory[conf][year][category] = []

    inventory[conf][year][category].append(recording)

  categories = {}
  allcategories = Category.query.all()
  for category in allcategories:
    categories[category.id] = category.description

  history = History.query \
    .filter_by(userid=user.id) \
    .filter_by(type='purchase') \
    .all()

  owned = {}
  for h in history:
    owned[h.recordingid] = True

  ios = isios(request)

  return render_template('start.html', credit=credit, 
    user=user, inventory=inventory, 
    owned=owned, ios=ios, categories=categories,
    currentyear=app.config['YEAR'])

@app.route("/store/buy/<id>", methods=['POST'])
def buy(id):
  if not auth():
    return jsonify(result=False, reason='auth')

  targetid = int(id)
  user = session['user']

  past = History.query \
    .filter_by(userid=user.id) \
    .filter_by(recordingid=targetid) \
    .first()

  if not past is None:
    return jsonify(result=False, reason='exists')

  recording = Recording.query.filter_by(id=targetid).first()

  if recording is None:
    return jsonify(result=False, reason='invalid')

  ppt = False
  if recording.ppt != '':
    ppt = True

  note = False
  if recording.note != '':
    note = True

  logs = get_logs(user)
  credit = get_credit(logs)

  if not credit['unlimited'] and credit['total'] <= 0:
    return jsonify(result=False, reason='credit')

  history = History('purchase', 1, -1, user.id, recording.title, recording.id)
  db.session.add(history)
  db.session.commit()

  if credit['unlimited']:
    total = 0
  else:
    total = credit['total'] - 1;
  
  return jsonify(result=True, id=targetid, note=note, ppt=ppt, total=total, unlimited=credit['unlimited'])

    
@app.route("/store/focus/<id>")
def focus(id):
  if not auth():
    return jsonify(result=False)

  user = session['user']
  logs = get_logs(user)
  credit = get_credit(logs)

  targetid = int(id)
  recording = Recording.query.filter_by(id=targetid).first()

  if recording is None:
    return jsonify(result=False)

  paragraphs = False
  if not recording is None:
    paragraphs = recording.description.split("\n")

  log = History.query \
    .filter_by(userid=user.id) \
    .filter_by(recordingid=targetid) \
    .first()

  owned = False
  if credit['unlimited'] or not log is None:
    owned = True

  ios = isios(request)

  thumburl = '/static/img/thumb.jpg'
  thumbdefault = True

  isstudy = False
  if recording.categoryid == 8:
    isstudy = True

  conf = 'chicago'
  if recording.conf == 1:
    conf = 'indy'

  if isstudy or recording.ppt != '':
    thumbdefault = False
    filepart = recording.filename.strip().split('.')    
    thumburl = '/static/img/thumbnail/' + conf + \
      '/' + filepart[0] + '.png'

  return jsonify(
    result=True,
    owned=owned,    
    id=recording.id,    
    thumbnail=thumburl,
    thumbdefault=thumbdefault,
    title=recording.title,
    speaker=recording.speaker,
    ppt=recording.ppt,
    note=recording.note,
    isstudy=isstudy,
    description=paragraphs
  )

def get_credit(logs):
  credit = {}

  credit['total'] = 0
  credit['paid'] = 0
  credit['unlimited'] = False

  for log in logs:
    credit['total'] += log.point
    if log.point > 0:
      credit['paid'] += log.point

  if credit['paid'] >= 25:
    credit['unlimited'] = True 

  if credit['paid'] > 25:
    credit['paid'] = 25

  return credit

def get_choices(credit):
  choices = {}
  choices['option'] = []
  choices['fullupgrade'] = 0

  if credit['paid'] < 20:
    if credit['paid'] == 15:
      choices['option'].append(5)
    else:
      choices['option'].append(5)
      choices['option'].append(10)

  choices['fullupgrade'] = 25 - credit['paid']
  return choices

def get_logs(user):
  logs = History.query \
    .filter_by(userid=user.id) \
    .order_by(History.id) \
    .all() 
  return logs

def render_points(error=False):
  if not auth():
    return render_template('login.html')

  user = session['user']  
  logs = get_logs(user)
  credit = get_credit(logs)
  choices = get_choices(credit)

  return render_template('points.html', 
    user=user, logs=logs, error=error, 
    credit=credit, choices=choices)  

@app.route("/store/points")
def points():
  return render_points()

@app.route("/store/<conf>/redeem", methods=['POST'])
def redeem(conf):
  conference = makeconf(conf)
  if not auth(conference):
    return render_template('login.html', conf=conference)

  user = session['user']
  giftcode = request.form['giftcode1'] + '-' + \
    request.form['giftcode2'] + '-' + \
    request.form['giftcode3'] + '-' + \
    request.form['giftcode4']

  code = Code.query \
    .filter_by(conf=conference['code']) \
    .filter_by(code=giftcode) \
    .first()

  codeerror=False
  if code is None:
    codeerror='notfound'

  elif code.userid > 0:
    codeerror='already'

  else:
    code.userid = user.id
    db.session.add(code)
    db.session.commit()

    history = History('gift', 1, code.credit, user.id, code.code, 0)
    db.session.add(history)
    db.session.commit()

  return render_points(conf, codeerror)

@app.route("/store/info")
def info():
  if not auth():
    return render_template('login.html')

  user = session['user']
  logs = get_logs(user)
  credit = get_credit(logs)

  return render_template('info.html', user=user, credit=credit)
