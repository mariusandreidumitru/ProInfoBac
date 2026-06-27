import urllib.request as u, json, sys

code = '''#include <iostream>\nusing namespace std;\nint main(){ cout<<"Hello"<<endl; return 0; }'''
data = json.dumps({'code': code, 'language': 'cpp'}).encode('utf-8')
req = u.Request('http://127.0.0.1:8001/compile', data=data, headers={'Content-Type':'application/json'})
try:
    with u.urlopen(req, timeout=20) as resp:
        body = resp.read().decode('utf-8')
        print('STATUS', resp.status)
        print(body)
except Exception as e:
    print('ERROR', e)
    sys.exit(1)
