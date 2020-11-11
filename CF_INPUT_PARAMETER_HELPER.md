# AWS CloudFormation Parameters



## S3

#### S3BucketName

This is the name of the bucket where all files are being copied for this utility. This will be populated for you based on bucket you used while making the build as mentioned in [DEVELOPMENT.md](./DEVELOPMENT.md)



#### ConfigurationFileKey

This is the path to configuration file used by the utility and is hosted as a DynamoDB table. A sample file is provided to help the understand the inputs. This configuration needs to be updated based on tables you want to manage in your Redshift cluster. The path to configuration file can be changed here, if needed.





## DynamoDB

#### DynamoDBTableName

This is the name fo the DynamoDB table that will host the configuration placed under ***ConfigurationFileKey*** parameter. A default name has been provided which can be changed as part of CloudFormation stack deployment.



#### DynamoDBTableProvisionedThroughputWCU

Provide number of provisioned throughput WCUs. These WCUs are only used to write content under ***ConfigurationFileKey*** parameter into the table mentioned under ***DynamoDBTableName*** parameter.

 

#### DynamoDBTableProvisionedThroughputRCU

Provide number of provisioned throughput RCUs. These WCUs are only used to read content from table mentioned under ***DynamoDBTableName*** parameter during every job run. Configuration is read once with each run of Glue python shell job mentionded under ***GlueJobName*** parameter.





## Redshift

#### RedshiftEndpointAddress, RedshiftEndpointPort, RedshiftDatabaseName, RedshiftMasterUserName

**Steps**:

- Login to **AWS Management Console**.

- Click **Services**.

- Click on **Redshift**. (You will land on Redshift dashboard page. Make sure you are in the correct region).

- Click on **Clusters** under Overview.

- Click on the Redshift cluster which needs to be managed with this utility.

- Click on **Properties**.

- **Master user name** (***RedshiftMasterUserName***) and **Endpoint** are mentioned on the right under **Connection details**. 

  Note: Endpoint is comprised of three parts and is of the form: <hostname>:<port>/<database name> 

  - Hostname (***RedshiftEndpointAddress***)
  - Port (***RedshiftEndpointPort***)
  - Database name (***RedshiftDatabaseName***)



#### RedshiftMasterPassword

This is the password associated with the master user password.



#### RedshiftSchemaName

This is the name of the schema which will be used to create stored procedure as part of the CloudFormation stack. 



#### RedshiftVPCId, RedshiftSubnetId, RedshiftAvailabilityZoneId, RedshiftSecurityGroupIds

**Steps**:

- Login to **AWS Management Console**.
- Click **Services**.
- Click on **Redshift**. (You will land on Redshift dashboard page. Make sure you are in the correct region).
- Click on **Clusters** under Overview.
- Click on the Redshift cluster which needs to be managed with this utility.
- Click on **Properties**.
- Scroll down to the **Network and security** portion.
- You will find here
  - VPC ID (***RedshiftVPCId***)
  - Availability Zone ID (***RedshiftAvailabilityZoneId***)
  - Security Groups (***RedshiftSecurityGroupIds***). More than one security group can be selected here.
- Click on subnet group name under **Subnet**.
- Check **Subnet ID** (for ***RedshiftSubnetId***) against corresponnding **Availability Zone**.



#### RedshiftSSL

**Steps**:

- Login to **AWS Management Console**.
- Click **Services**.
- Click on **Redshift**. (You will land on Redshift dashboard page. Make sure you are in the correct region).
- Click on **Clusters** under Overview.
- Click on the Redshift cluster which needs to be managed with this utility.
- Click on **Properties**.
- Scroll down and click on paramater name under **parameter** in **Database configurations** section.

- Click on **Parameters **(beside **Workload management**).
- Check **require_ssl** paramater value.
- If this is set to true, cluster is enabled with SSL and if false, cluster is not enabled with SSL. (***RedshiftSSL***)



#### RedshiftSelfReferencingSecurityGroupRule

This parameter, if set to **true**, let CloudFormation stack create a self-referencing rule in Redshift security group mentioned under ***RedshiftSecurityGroupIds*** parameter that allows Glue job mentioned under ***GlueJobName*** parameter to connect to the Redshift cluster mentioned under ***RedshiftEndpointAddress*** parameter. Select **false**, if a self-referencing rule already exists in the Redshift security group. Read more about Glue VPC access [here](https://docs.aws.amazon.com/glue/latest/dg/setup-vpc-for-glue-access.html). 





## Secrets Manager

#### RedshiftSecretManagerFlag

This parameter, if set to **true**, let CloudFormation stack create a Redshift secret in Secrets Manager mentioned under ***RedshiftEndpointAddress*** parameter. It allows the lambda function (**RedshiftDataLCManagementProcedureCreation**) created by CloudFormation stack to securely connect to Redshift cluster and create PL/pgSQL stored procedure. Select **false**, if a secret already exist for the Redshift cluster. 



#### RedshiftSecretManagerName

If you already have a secret for the Redshift cluster set up then use the below mentioned steps to get the name of the connection.

**Steps**:

- Login to **AWS Management Console**.
- Click **Services**.
- Click **Secrets Manager**.
- All secrets are listed under **Secret name**.
- Chose the secret corresponding to the Redshift cluster.

<u>Note</u>: Leave this paramater blank if you selected **true** under **RedshiftSecretManagerFlag** parameter.



#### RedshiftSecretManagerEndpointFlag

This flag let CloudFormation stack know if it needs to create a Secret Manager Endpoint with the VPC where Redshift is hosted. If a Secret Manager Endpoint already exists with this VPC, select **false**. If not, then select **true** and, let the CloudFormation stack create a Secret Manager End point with the VPC where Redshift is hosted.

<u>Note</u>: Check all existing Endpoints under **VPC** >> **Endpoints** in **AWS Management Console**.





## Glue

#### GlueJobName

This is the name of the Glue python shell job that the CloudFormation stack will create. A default name is provided but a different name can be provided as well.



#### GlueRedshiftConnectionFlag

This flag is used to create Redshift connection under Glue Connection, if one does not already exists. Chose **true** to let CloudFormation stack create one for you or set this parameter to false and give the name of the existing Redshift Glue connection under ***GlueRedshiftConnectionName*** parameter.



#### GlueRedshiftConnectionName

If you already have a Glue Redshift connection set up then use the below mentioned steps to get the name of the connection.

**Steps**:

- Login to AWS Management Console.
- Click **Services**.
- Click on **Glue**.
- Click on **Connections** under **Databases** from left pane menu.
- All connection names are listed under **Name** (***GlueRedshiftConnectionName***). Double check the connection details by clicking on the connection name and verify the connection details.

<u>Note</u>: Leave this paramater blank if you selected **true** under **GlueRedshiftConnectionFlag** parameter.





## VPC Endpoint

#### S3VPCEndpointFlag

This flag let CloudFormation stack know if it needs to create a S3 VPC Endpoint with the VPC where Redshift is hosted. If a S3 Endpoint already exists with this VPC, select **false**. If not, then select **true** and, let the CloudFormation stack create a S3 Endpoint with the VPC where Redshift is hosted.



#### DynamoDBVPCEndpointFlag

This flag let CloudFormation stack know if it needs to create a DynamoDB VPC Endpoint with the VPC where Redshift is hosted. If a DynamoDB VPC Endpoint already exists with this VPC, select **false**. If not, then select **true** and, let the CloudFormation stack create a DynamoDB VPC Endpoint with the VPC where Redshift is hosted.



#### VPCRouteIDs

**Steps**:

- Login to AWS Management Console.
- Click **Services**.
- Click on **Redshift**. (You will land on Redshift dashboard page. Make sure you are in the correct region).
- Click on **Clusters** under Overview.
- Click on the Redshift cluster which needs to be managed with this utility.
- Click on **Properties**.
- Scroll down to the **Network and security** portion.
- Click on VPC ID that will take you to the VPC page.
- Check against the vpc and scroll down to see route id under **Route table**.

