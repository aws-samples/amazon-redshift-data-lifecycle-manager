import boto3
import pg8000
import os
import json
from botocore.exceptions import ClientError


s3 = boto3.resource('s3')
bucket_name = os.environ['ConfigBucket']
file_ref_path = os.environ['sqlScriptKey']
redshift_schema_name = os.environ['redshiftSchemaName']

pg8000.paramstyle = "qmark"

def get_redshift_conn():
    secret = os.environ['redshiftSecretName']
    secret_manager = boto3.client('secretsmanager')
    try:
        secret = secret_manager.get_secret_value(SecretId=secret)
        secret_string = json.loads(secret['SecretString'])
    except ClientError as e:
        try:
            error_code = e.response['Error']['Code']
        except KeyError:
            # The intention here is to ignore the KeyError and raise the
            # original ClientError exception. This avoids polluting the
            # traceback with the KeyError
            raise e
        if error_code == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the 
            # provided KMS key. Deal with the exception here, and/or rethrow at 
            # your discretion.
            raise
        elif error_code == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise
        elif error_code == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise
        elif error_code == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current 
            # state of the resource. Deal with the exception here, and/or 
            # rethrow at your discretion.
            raise
        elif error_code == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise
        else:
            raise
    rs_host = secret_string['host']
    rs_port = secret_string['port']
    rs_database = secret_string['database']
    rs_user = secret_string['username']
    rs_password = secret_string['password']
    ssl_mode = os.environ['redshiftSSL']
    if ssl_mode == 'true':
        conn = pg8000.connect(database=rs_database, host=rs_host, port=rs_port, \
                              user=rs_user, password=rs_password, ssl_context=True)
    else:
        conn = pg8000.connect(database=rs_database, host=rs_host, port=rs_port, \
                              user=rs_user, password=rs_password)
    print('Connected to Redshift cluster')
    conn.autocommit = True
    # create a new cursor for methods to run through
    cursor = conn.cursor()
    return cursor, conn


def lambda_handler(event, context):
    obj = s3.Object(bucket_name, file_ref_path)
    # read content of sql script
    script = obj.get()['Body'].read().decode()
    # Replace schema variable in Redshift with schema name entered through
    # CloudFormation stack
    script = script.replace('SCHEMAVARIABLE', redshift_schema_name)
    # Establish connection to Redshift cluster using connection details
    # retrieved from Secrets Manager
    conn = None
    try:
        cursor, conn = get_redshift_conn()
        # Execute sql.
        cursor.execute(script)
        conn.commit()
        print('PL/pgSQL procedure has successfully created in Redshift')
        cursor.close()
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()
