import random

for i in range(0,4000):
  code = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(16))
  coupon = code[:4] + "-" + code[4:8] + "-" + code[8:12] + "-" + code[12:]
  print "INSERT INTO code (code) VALUES ('" + coupon + "');"

