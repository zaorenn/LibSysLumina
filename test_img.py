import requests

isbns = [
    '9780739409558',
    '0871294273',
    '9780812421453',
    '9789754704723'
]

for isbn in isbns:
    # Test HTTP
    url_http = f"http://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
    try:
        r = requests.get(url_http, timeout=5)
        print(f"ISBN {isbn} (HTTP): Status {r.status_code}, Length {len(r.content)} bytes")
    except Exception as e:
        print(f"ISBN {isbn} (HTTP) Failed: {e}")

    # Test HTTPS
    url_https = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
    try:
        r = requests.get(url_https, timeout=5)
        print(f"ISBN {isbn} (HTTPS): Status {r.status_code}, Length {len(r.content)} bytes")
    except Exception as e:
        print(f"ISBN {isbn} (HTTPS) Failed: {e}")
