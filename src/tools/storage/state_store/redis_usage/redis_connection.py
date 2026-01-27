import redis
from src.configs.settings import reddis_host, reddis_port, reddis_password, reddis_username

redis_connection = redis.Redis(host=reddis_host,
                               port=reddis_port,
                               #db=0,
                               decode_responses=True,
                               username=reddis_username,
                               password=reddis_password
                               )