import requests

session = requests.Session()
# Setup session with headers
headers = {
    'Accept': 'application/json',
    'Authorization': 'Bearer DUMMY'
}
session.headers.update(headers)

# make the same request
import time
start_time = time.time()
for _ in range(10):
    session.get('https://httpbin.org/anything/test')
end_time = time.time()
print(f"Time taken for 10 requests with Session: {end_time - start_time:.4f} seconds")
