import boto3
from datetime import datetime, timezone

class Vault():
    """
    A class to interact with an AWS Backup Vault through boto3
    """
    
    def __init__(self, 
                 vault_name, 
                 account=boto3.client('sts').get_caller_identity().get('Account'), 
                 region='us-east-1'):
        """
        Parameters
        ---------
        vault_name : str
            the name of the AWS Backup vault
        account : str
            the name of the AWS account the Backup Vault is located
        region : str
            the name of the AWS region the Backup Vault is located  
        """
        self.vault_name = vault_name
        self.account = account
        self.client = boto3.client('backup')
        self.region = region
        
    def list_backups(self, 
                     resource_type='All', 
                     created_before=datetime.now(timezone.utc), 
                     created_after=datetime(2015, 1, 1)):
        """
        Lists the Recovery Points in the Vault based on the provided information
        
        Parameters
        ----------
        resource_type : str
            The AWS resource type for the recover point. Accepted values are:
                Aurora
                DocumentDB
                CloudFormation
                DynamoDB
                EBS
                EC2
                EFS
                FSx
                Neptune
                RDS
                Redshift
                S3
                Timestream
                VirtualMachine
            
        created_before : str, datetime
            This is used to search for recovery points created before a date
            Options for usage are string format eg. '2024-01-01' or datetime(2024, 1, 1)
            
        created_after : str, datetime
            This is used to search for recovery points created after a date
            Options for usage are string format eg. '2024-01-01' or datetime(2024, 1, 1)
        """
        if resource_type == 'All':
            response = self.client.list_recovery_points_by_backup_vault(
                BackupVaultName=self.vault_name,
                ByCreatedBefore=created_before,
                ByCreatedAfter=created_after
            )
        else:
            response = self.client.list_recovery_points_by_backup_vault(
                BackupVaultName=self.vault_name,
                ByResourceType=resource_type,
                ByCreatedBefore=created_before,
                ByCreatedAfter=created_after
            )
            
        return response
    
    def copy_backups(self, 
                     destination_vault,
                     recovery_point,
                     region='us-east-1',
                     dest_account=boto3.client('sts').get_caller_identity().get('Account'),
                     retention_period=35):
        """
        Copies a Recovery Point in the Vault to a different Vault in the same or different region
        
        Parameters
        ----------
        destination_vault : str
            The Vault the Recovery Point is to be copied to
            
        recovery_point : str
            The Recovery Point ARN that is to be copied
            
        region : str
            The AWS region that the destination Vault is located
            
        dest_account : str
            The AWS account the destination Vault is located
            
        retention_period : int
            The length of time (in days) the Recovery Point will remain in the Vault before deletion
        """
        
        response = self.client.start_copy_job(
            RecoveryPointArn=recovery_point,
            SourceBackupVaultName=self.vault_name,
            DestinationBackupVaultArn=f'arn:aws:backup:{region}:{dest_account}:backup-vault:{destination_vault}',
            IamRoleArn=f'arn:aws:iam::{self.account}:role/service-role/AWSBackupDefaultServiceRole',
            Lifecycle={
                'DeleteAfterDays': retention_period
            }
        )
        
        return response
        
    def restore_ebs(self, 
                    recovery_point, 
                    az='us-east-1a',
                    iops='3000',
                    kms_key=None,
                    throughput='125',
                    vol_type='gp3'):
        
        """
        Restores an EBS volume from a Recovery Point
        
        Parameters
        ----------          
        recovery_point : str
            The Recovery Point ARN that is to be restored
            
        az : str
            The AWS availability zone the EBS volume will be restored to
            
        iops : str
            The IOPS for the EBS volume
            
        kms_key : str
            The ARN for the KMS key that will encrypt the EBS volume
        
        throughput : str
            The throughput for the EBS volume
            
        vol_type : str
            The volume type for the EBS volume         
        """
        
        rec_point_desc = self._describe_backup(recovery_point)
        if rec_point_desc['IsEncrypted'] == True:
            encrypted = 'true'
        else:
            encrypted = 'false'
        
        if encrypted == 'true' and kms_key == None:
            kms_key = rec_point_desc['EncryptionKeyArn']
                   
        if encrypted == 'true' or kms_key:
            metadata = {
                "availabilityzone": az,
                "encrypted": encrypted,
                "iops": iops,
                "kmskeyid": kms_key,
                "throughput": throughput,
                "volumesize": str(self._get_vol_size(recovery_point)),
                "volumetype": vol_type
            }
        else:
            metadata = {
                "availabilityzone": az,
                "encrypted": encrypted,
                "iops": iops,
                "throughput": throughput,
                "volumesize": str(self._get_vol_size(recovery_point)),
                "volumetype": vol_type
            }
        
        response = self.client.start_restore_job(
            RecoveryPointArn=recovery_point,
            Metadata=metadata,
            IamRoleArn=f'arn:aws:iam::{self.account}:role/service-role/AWSBackupDefaultServiceRole',
            CopySourceTagsToRestoredResource=True
        )
        
        restore = self.client.describe_restore_job(
            RestoreJobId=response['RestoreJobId']
        )
        
        return restore
    
    def restore_ec2(self, 
                    recovery_point, 
                    instance_type, 
                    key_name, 
                    vpc_id, 
                    subnet_id):
        
        """
        Restores an EC2 Instance from a Recovery Point
        
        Parameters
        ----------          
        recovery_point : str
            The Recovery Point ARN that is to be restored
            
        instance_type : str
            The instance type for the restored EC2
            
        key_name : str
            The key pair to be used for the restored EC2
            
        vpc_id : str
            The VPC ID the restored EC2 will be placed
        
        subnet_id : str
            The subnet ID the restored EC2 will be placed      
        """
        
        metadata = {
            "instancetype": instance_type,
            "keyname": key_name,
            "vpcid": vpc_id,
            "subnetid": subnet_id
        }
        
        response = self.client.start_restore_job(
            RecoveryPointArn=recovery_point,
            Metadata=metadata,
            IamRoleArn=f'arn:aws:iam::{self.account}:role/service-role/AWSBackupDefaultServiceRole',
            CopySourceTagsToRestoredResource=True
        )
        
        return response
                
    def _get_vol_size(self, recovery_point):
        vol_size = self.client.describe_recovery_point(
            BackupVaultName=self.vault_name,
            RecoveryPointArn=recovery_point
        )
        
        return int(vol_size['BackupSizeInBytes']/1024/1024/1024)
    
    def _describe_backup(self, recovery_point):
        response = self.client.describe_recovery_point(
            BackupVaultName=self.vault_name,
            RecoveryPointArn=recovery_point
        )
        
        return response