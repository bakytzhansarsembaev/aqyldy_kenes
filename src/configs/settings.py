import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# openai configs
OPENAI_API_KEY_BASE = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY_TASK_HELPER = os.getenv("OPENAI_API_KEY_TASK_HELPER", OPENAI_API_KEY_BASE)
ASSISTANT_ID_RUS = 'asst_8VyYl7hjshNOI3zwifUCrNal'
ASSISTANT_ID_KAZ = 'asst_po2uHM4YGXasWM3D9GKRPB62'


# API configs
PROD_URL = 'https://qalan.kz'
TEST_URL = 'https://test.qalan.kz'
ML_RESPONSE = '{}/api/mlResponse'

# gpt_models
gpt_model_4o = "gpt-4o"
gpt_model_4o_mini = "gpt-4o-mini"
gpt_model_4_1 = "gpt-4.1"
gpt_model_4_1_mini = "gpt-4.1-mini"
gpt_model_5 = "gpt-5"
gpt_5_1 = "gpt-5.1"
gpt_5_2 = "gpt-5.2"


# !!!ОБЯЗАТЕЛЬНО УКАЗЫВАТЬ, ЧТОБ БЫЛО ОЧЕВИДНО, КУДА СТУЧАТЬСЯ!!!
USABLE_BRANCH = PROD_URL
DEFAULT_GPT_MODEL = gpt_model_5

# Mock mode для тестирования без API
USE_MOCK_SERVICES = os.getenv("USE_MOCK_SERVICES", "true").lower() == "true"

# Language: "ru" / "kz"
ASSISTANT_LANGUAGE = "kz"

# dateFormat
date_format = '%Y-%m-%d %H:%M:%S'

# RABBIT configs
PROD_RABBIT = 'amqp://admin:FuzXKWUV3Mos4h4T3E@10.207.48.24:5672/admin'
TEST_RABBIT = 'amqp://rmuser:U5WD9kHYm5c3pwqn@10.207.19.4:5672/rmuser'
RABBIT_TEST_QUEUE = "test_messages"
RABBIT_PROD_QUEUE = "messages"
RABBIT_RUSSIAN = "messages_rus"

USABLE_RABBIT_URL = PROD_RABBIT
USABLE_RABBIT_QUEUE = RABBIT_TEST_QUEUE

# Qalan.kz API main_token
MAIN_TOKEN = os.getenv("QALAN_MAIN_TOKEN")
headers1 = {"Authorization" : "Bearer {}".format(MAIN_TOKEN)}


# redis_connection_auth
#reddis_host = "10.207.19.7"
#reddis_port = 6379
#reddis_username = "username"
#reddis_password = "password"

# redis_connection_auth
reddis_host = "redis-17941.c124.us-central1-1.gce.cloud.redislabs.com"
reddis_port = 17941
reddis_username = "default"
reddis_password = "8G1Tqn0jq3NFCIfj7MK48GpKgpGlR48B"


# Qalan API's
USER_LOGIN_PASSWORDS_URL = USABLE_BRANCH + '/api/dataScience/users/{}' # format(user_id)
USER_FREEZINGS = USABLE_BRANCH + '/api/users/{}/newFreezings' # format(user_id)
USER_CASHBACKS = USABLE_BRANCH + '/api/users/{}/personalStudy/cashbacks' # format(user_id)
USER_PAYMENTS = USABLE_BRANCH + '/api/users/{}/payments' # format(user_id)
USER_PAYOUTS = USABLE_BRANCH + '/api/users/{}/payouts' # format(user_id)
USER_DAILY_PERSONAL_STUDY = USABLE_BRANCH + '/currentTeacher/personalStudy/items?pupilUserIds[]={}' #format(user_id)
USER_TASK_SECTION = USABLE_BRANCH + '/api/mlResponse/personalStudyByUserId?userId={}'
USER_CURRENT_TASK = USABLE_BRANCH + '/api/mlRequest/pupilInfo?userId={}'
