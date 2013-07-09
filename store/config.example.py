from store import app

app.secret_key = 'anysecrect'
app.config.update(
  DEBUG=True,
  YEAR=2013,
  SECRET="somesecret",
  SQLALCHEMY_DATABASE_URI='mysql://user:pass@localhost/store',
  ADMINPASS="adminsecret",
  STRIPE_API_KEY='stripkeygivenbystrip',
  AWS_ACCESS_KEY_ID = 'awsid',
  AWS_SECRET_ACCESS_KEY = 'awsaccesskey'
)
