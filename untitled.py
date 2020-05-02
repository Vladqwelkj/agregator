import requests
import time
import threading
import json



def in_new_thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper

y = []

#@in_new_thread
def f():
	
	x=2
	for _ in range(27):
		x = x**2
	y.append(1)
	print(1)

N  =15
t = time.time()
for _ in range(N):
	f()

while len(y)<N:
	time.sleep(0.001)

print(time.time()-t)