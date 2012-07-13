from store import app

from time import time
import base64
import hmac, sha
import urllib

def url(bucket, key, secondsAlive):
	expires = int(time()) + secondsAlive
	canonicalizedResource = urllib.quote("/" + bucket + "/" + key)
	stringToSign = "GET\n\n\n" + str(expires) + "\n" + canonicalizedResource
	signature = base64.b64encode(hmac.new(app.config['AWS_SECRET_ACCESS_KEY'], stringToSign, sha).digest())
	return "http://"+bucket+".s3.amazonaws.com/"+urllib.quote(key)+ \
    "?AWSAccessKeyId="+urllib.quote(app.config['AWS_ACCESS_KEY_ID'])+ \
    "&Expires="+str(expires)+"&Signature="+urllib.quote(signature)


