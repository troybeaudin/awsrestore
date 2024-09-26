from .vault import Vault
import boto3

def check_aws_credentials():
    try:
        client = boto3.client('sts')
        response = client.get_caller_identity()
    except Exception as error:
        print("No valid credentials found")
        

check_aws_credentials()