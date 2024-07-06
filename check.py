import requests

response = requests.get('http://localhost:8000/')

if 'Access-Control-Allow-Origin' in response.headers:
    print(f"CORS is configured. Allowed origins: {response.headers['Access-Control-Allow-Origin']}")
    print(response.headers)
else:
    print("CORS is not configured.")
    print(response.headers)
