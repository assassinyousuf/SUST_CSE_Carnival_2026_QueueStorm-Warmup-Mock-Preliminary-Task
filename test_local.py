import urllib.request, json

def test(url, data=None):
    try:
        if data:
            req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url)
        print(urllib.request.urlopen(req).read().decode())
    except Exception as e:
        print("Error:", e)

print("== HEALTH ==")
test('http://127.0.0.1:8080/health')

print("\n== TICKET 1 ==")
test('http://127.0.0.1:8080/sort-ticket', {"ticket_id": "T-001", "message": "I sent 3000 to wrong number"})

print("\n== TICKET 3 ==")
test('http://127.0.0.1:8080/sort-ticket', {"ticket_id": "T-003", "message": "Someone called asking my OTP, is that bKash?"})
