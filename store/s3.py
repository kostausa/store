from time import time
import base64
import hmac, sha
import urllib

AWSAccessKeyId = 'AKIAIVD52EDQ5XLSF7GA'
AWSSecretAccessKey = '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'

def url(bucket, key, secondsAlive):
	expires = int(time()) + secondsAlive
	canonicalizedResource = urllib.quote("/" + bucket + "/" + key)
	stringToSign = "GET\n\n\n" + str(expires) + "\n" + canonicalizedResource
	signature = base64.b64encode(hmac.new(AWSSecretAccessKey, stringToSign, sha).digest())
	return "http://"+bucket+".s3.amazonaws.com/"+urllib.quote(key)+ \
    "?AWSAccessKeyId="+urllib.quote(AWSAccessKeyId)+ \
    "&Expires="+str(expires)+"&Signature="+urllib.quote(signature)

