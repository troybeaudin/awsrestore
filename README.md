# AWSRestore
awsrestore is Python module in the form of an AWS API wrapper that will allow you to easily interact with AWS Backup Vaults.

When dealing with restoring data during an outage or cyber attack, time is one of the most important factors. This module will help reduce the time and effort to get systems and data in AWS available by limiting the information you need to provide while allowing for flexibility. 

## Installation
Requires Python3 and [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#installation)

```
pip install -r requirements.txt
```

## Quickstart
Using the downloaded code, import the module
```
import awsrestore

# Instantiate the class
vault = awsrestore.Vault('vault-1')

# Lists the EBS backups created between Jan 1 and Jan 2, 2024
backups = vault.list_backups(resource_type='EBS', created_before='2024-01-02', created_after='2024-01-01')

# Iterates through the list of backups and then starts the restore
for backup in backups['RecoveryPoints']:
    vault.restore_ebs(backup['RecoveryPointArn'])
```

## Planned Features
- Add support for restoring the other resource types
- Allow creation of vault policies
- Create and start backup jobs