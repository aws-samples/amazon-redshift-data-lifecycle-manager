Build and Deploy
----------------

Clone the git repository in your environment.

<u>Note</u>: Git must be installed in your environment.

```shell
cd <directry path>
git clone <repository URL>
```

Then, in the project's root directory, run:

```shell
make build
```

This will ask you for an existing Amazon S3 bucket name that will be used to host the files created by the utility. AWS CloudFormation template will refer these files while deployment. 

Build creates following files and upload it to the provided S3 bucket.

1. Zip file for DynamoDB writer (**csv-DynamoDB-Redshift-data-lc-management-config-writer**) lambda function.
2. Zip file for Redshift DDL creation (**RedshiftDataLCManagementProcedureCreation**) 
3. AWS Glue Management job
4. AWS Glue Reference egg file
5. Amazon Redshift PL/pgSQL procedure DDL function.
6. Sample configuration file to be loaded in DynamoDB.
7. AWS CloudFormation template for the deployment.

Use the CloudFormation URL produced after running build command and deploy it through AWS Management console. 

Click [here](./CF_INPUT_PARAMETER_HELPER.md) to know more about paramaters used in CloudFormation stack.

Once CloudFormation stack is deployed successfully, continue from **Deployment Steps** in [README.md](./README.md).



## Modifying validator

###### [validator.py](config/validator.py) file is used to validate the configuration being loaded to DynamoDB by DynamoDB writer lambda function and read by AWS Glue Management job.



### If you need to change validator.py file

Build process also provides flexibility to modify validator.py file, in case you need to edit it.

Run the following commands to enforce new validator.py file.

```shell
make validate
```



<u>Note</u>: Above command needs to be run in Python3.6 environment. 

If you have already deployed the stack with default validator.py file and you changed it, then you need to delete the stack and redeploy it. Run the build again to get AWS CloudFormation URL for deployment.

```shell
make build
```



Use the URL produced after running build command and deploy it through AWS Management console. Once CloudFormation stack is deployed successfully, continue from **Deployment Steps** in [README.md](./README.md).



