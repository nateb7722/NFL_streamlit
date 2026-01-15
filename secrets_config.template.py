"""
AWS Configuration Template
Copy this file to secrets_config.py and fill in your credentials.
DO NOT commit secrets_config.py to version control!
"""
import os

os.environ['AWS_ACCESS_KEY_ID'] = 'YOUR_ACCESS_KEY_ID'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'YOUR_SECRET_ACCESS_KEY'
os.environ['AWS_S3_BUCKET'] = 'YOUR_BUCKET_NAME'
os.environ['ENVIRONMENT'] = 'Prod'
