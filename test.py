"""Basic connection example.
"""

import redis

r = redis.Redis(
    host='redis-17941.c124.us-central1-1.gce.cloud.redislabs.com',
    port=17941,
    decode_responses=True,
    username="default",
    password="8G1Tqn0jq3NFCIfj7MK48GpKgpGlR48B",
)

success = r.set('foo', 'bar')
# True

result = r.get('foo')
print(result)
# >>> bar

