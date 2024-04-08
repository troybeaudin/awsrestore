from .vault import Vault
import boto3

def check_aws_credentials():
    session = boto3.Session()
    credentials = session.get_credentials()
    
    if credentials is None or credentials.access_key is None or credentials.secret_key:
        return False
    
    return True

if not check_aws_credentials:
    print("There doesn't appear to be valid AWS credentials")