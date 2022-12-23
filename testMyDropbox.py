import requests


URL = {'PUT': 'https://4kbgpzpyb2.execute-api.ap-southeast-1.amazonaws.com/default/upload-s3', 'VIEW':'https://im0ukagl96.execute-api.ap-southeast-1.amazonaws.com/default/act4',
'GET': 'https://cjpg12qh5j.execute-api.ap-southeast-1.amazonaws.com/default/get-s3' }


fn = 'tent:test.txt'
BODY = {'file_name': fn}

response = requests.get(url = URL['GET'], json = BODY)
print(response.text)
a = requests.get(url = response.text)
open(fn, 'wb').write(a.content)
