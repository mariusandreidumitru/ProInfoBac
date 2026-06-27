import requests, json
payload={
    "language":"cpp",
    "version":"10.2.0",
    "files":[{"name":"main.cpp","content":"#include <iostream>\nusing namespace std;\nint main(){ cout<<\"Hello\"<<endl; return 0; }"}],
    "stdin":""
}
r = requests.post('https://emkc.org/api/v2/piston/execute', json=payload, timeout=15)
print('STATUS', r.status_code)
try:
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception:
    print('RAW', r.text)
