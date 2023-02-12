# Reference: https://stackoverflow.com/a/67122583/7044793

import os
from google.auth.transport import requests
from google.oauth2 import id_token

# Set this env with path to service account credentials file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/service-account-credentials.json'

request = requests.Request()
audience = 'my_cloud_function_url'

token = id_token.fetch_id_token(request, audience)
