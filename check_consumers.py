import requests

RABBIT_HOST = '10.207.48.24'
RABBIT_USER = 'admin'
RABBIT_PASS = 'FuzXKWUV3Mos4h4T3E'
VHOST = 'admin'
QUEUE = 'test_messages'

url = f'http://{RABBIT_HOST}:15672/api/queues/{VHOST}/{QUEUE}'

r = requests.get(url, auth=(RABBIT_USER, RABBIT_PASS))
data = r.json()

print(f"Queue: {QUEUE}")
print(f"Consumers: {data.get('consumers', 0)}")
print(f"Messages ready: {data.get('messages_ready', 0)}")
print(f"Messages unacked: {data.get('messages_unacknowledged', 0)}")

if 'consumer_details' in data:
    print("\nConsumer details:")
    for c in data['consumer_details']:
        print(f"  - {c.get('consumer_tag')} @ {c.get('channel_details', {}).get('peer_host', '?')}")
