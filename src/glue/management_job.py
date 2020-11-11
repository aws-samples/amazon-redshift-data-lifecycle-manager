"""
REDSHIFT DATA LIFECYCLE MANAGEMENT
"""
from typing import Tuple

import boto3
from pgdb import connect
import json
import sys
from awsglue.utils import getResolvedOptions

from validator.validator import ConfigRecord


def sort_priority(metadata):
    """
    Function to fetch priority of tables from each item in the configuration
    """
    try:
        return int(metadata['priority'])
    except KeyError:
        return 0


def _get_rs_cursor(secret):
    secrets = boto3.client('secretsmanager')
    secret = secrets.get_secret_value(SecretId=secret)
    secret_string = json.loads(secret['SecretString'])
    rs_conn = connect(
        host=secret_string["host"],
        port=secret_string["port"],
        database=secret_string["database"],
        user=secret_string["username"],
        password=secret_string["password"]
    )
    cursor = rs_conn.cursor()
    cursor.execute("set statement_timeout = 1200000")
    return rs_conn, cursor


def _get_all_items(table):
    all_items = list()
    last_evaluated_key = None
    while True:
        if last_evaluated_key:
            response = table.scan(ExclusiveStartKey=last_evaluated_key)
        else:
            response = table.scan()
        all_items += response['Items']
        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break
    all_items.sort(key=sort_priority)
    return all_items


def _generate_procedure_call(row: ConfigRecord,
                             redshift_schema: str,
                             role_arn: str,
                             region_name: str):
    if not len(row.partition_column):
        partition_column = ""
    else:
        partition_column = f" PARTITION BY ({row.partition_column})"
    if not row.checkpoint or row.checkpoint.lower() == "none":
        checkpoint = "None"
    else:
        checkpoint = row.checkpoint
    if len(row.unload_region):
        region_name = row.unload_region
    if not row.file_format:
        # TODO: what happens if row['header'], row['delimiter'] and/or
        #   row['add_quotes'] are all empty values?
        file_format = ''
        if str(row.header) == '1':
            file_format += "HEADER"
        if row.delimiter:
            file_format += f" DELIMITER AS ''{row.delimiter}''"
        if str(row.add_quotes) == '1':
            file_format += " ADDQUOTES"
        if row.null_as:
            file_format += f" NULL AS '{row.null_as}'"
        if str(row.escape) == '1':
            file_format += " ESCAPE"
        if row.compression:
            file_format += f" {row.compression}"
    elif row.file_format.lower() == "csv":
        file_format = "CSV"
        if str(row.header) == '1':
            file_format += "HEADER"
        if row.delimiter:
            file_format += f" DELIMITER AS ''{row.delimiter}''"
        if str(row.null_as) == '1':
            file_format += f" NULL AS '{row.null_as}'"
        if row.compression:
            file_format += f" {row.compression}"
    elif row.file_format.lower() == "parquet":
        file_format = "PARQUET"
    else:
        # Note: This will raise a KeyError if no file_format attribute is found
        file_format = row.file_format
    if str(row.parallel) == '0':
        parallel = "PARALLEL OFF"
    else:
        parallel = " "
    # Return a procedure call string to be executed against Redshift
    return (
        f"call {redshift_schema}.rs_data_lc_manager('{row.schema_name}',"
        f"'{row.table_name}','{row.column_name}',"
        f"'{row.granularity_level}',{row.retention_period},"
        f"'{row.s3_path}','{file_format}','{partition_column}',"
        f"'{role_arn}','{region_name}','{row.max_filesize}',"
        f"'{parallel}',{row.update_delete_flag},'{checkpoint}');"
    )


def _execute_procedure_call(row: ConfigRecord, procedure_call: str, cursor):
    print("\n*************************************************")
    print(f"TABLE: {row.schema_name}.{row.table_name}")
    print("*************************************************")
    # execute Redshift procedure and log audit results
    cursor.execute(procedure_call)
    return cursor.fetchone()


def _update_checkpoint(table, row: ConfigRecord, audit_results):
    if audit_results[2]:
        table.update_item(
            Key={
                'schema_name': row.schema_name,
                'table_name': row.table_name
            },
            UpdateExpression="SET checkpoint= :var1",
            ExpressionAttributeValues={
                ':var1': str(audit_results[2])
            }
        )
        print(
            f"INFO: Updated the checkpoint from: "
            f"{row.checkpoint} to: {audit_results[2]}"
        )


def _report_results(row: ConfigRecord, audit_results: Tuple):
    if row.granularity_level.lower() == "daily":
        day_month = "day(s)"
    elif row.granularity_level.lower() == "monthly":
        day_month = "month(s)"
    else:
        day_month = "Invalid"
    if int(row.update_delete_flag) == 0:
        print(
            f"INFO: Unloaded {audit_results[0]} {day_month} of data "
            f"comprising {audit_results[1]} row(s) to s3 location: "
            f"{row.s3_path}"
        )
    elif int(row.update_delete_flag) == 1:
        print(
            f"INFO: Deleted {audit_results[0]} {day_month} of data "
            f"comprising {audit_results[1]} row(s)"
        )
    elif int(row.update_delete_flag) == 2:
        print(
            f"INFO: Unloaded and Deleted {audit_results[0]} {day_month} "
            f"of data comprising {audit_results[1]} row(s) to "
            f"s3 location: {row.s3_path}"
        )
    else:
        print("ERROR: Invalid update_delete_flag in the configuration")


def _vacuum(row: ConfigRecord, cursor):
    """
    Run explicit vacuum and analyze on table after unloading and
    deleting data from Redshift
    """
    vacuum_query = (
        f"commit;vacuum {row.schema_name}.{row.table_name};commit;"
    )
    analyze_query = f"analyze {row.schema_name}.{row.table_name};"
    cursor.execute(vacuum_query)
    print("INFO: Vacuum done successfully")
    cursor.execute(analyze_query)
    print("INFO: Statistics update done successfully")


def main(args):
    # Get a connection and cursor against Redshift
    rs_conn, rs_cursor = _get_rs_cursor(args['secret'])
    # Use boto3 to interact with DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=args['region_name'])
    table = dynamodb.Table(args['dynamodb_table_name'])
    # Get all the config items from DynamoDB
    config_items = _get_all_items(table)
    for row in config_items:
        # Validate the data in the row
        row = ConfigRecord(**row)
        # Generate a procedure call based on the most recent checkpoint
        # in DynamoDB
        procedure_call = _generate_procedure_call(
            row,
            args['redshift_schema'],
            args['role_arn'],
            args['region_name']
        )
        # Execute the procedure call against Redshift and return the audit
        # results
        try:
            audit_results = _execute_procedure_call(
                row,
                procedure_call,
                rs_cursor
            )
            _report_results(row, audit_results)
        except Exception as e:
            print(f"ERROR: An exception has occurred: {e}")
            rs_conn.commit()
            continue
        # Update the checkpoint record in DynamoDB with the audit results from
        # the execution call
        try:
            _update_checkpoint(table, row, audit_results)
        except Exception as e:
            print(
                f"ERROR: An exception has occurred while updating "
                f"the checkpoint: {e}"
            )
            continue
        # Vacuum cannot be executed within a stored procedure or
        # transactional block. We won't reach this call if there has been
        # an exception
        try:
            _vacuum(row, rs_cursor)
        except Exception as e:
            print(f"ERROR: Vacuuming failed: {e}")
    # At this point, we have at least tried to process every single config row
    # in DynamoDB. Every row will have been processed successfully, or an
    # exception will have been printed to CloudWatch. Therefore, this code
    # will always run
    rs_cursor.close()
    rs_conn.close()
    print("\n\nRedshift connection is closed")


if __name__ == '__main__':
    # Get Job arguments for Redshift Secrets Manager Secret Name (secret)
    # for accessing Redshift, Redshift role arn (role_arn) and region name
    # (region_name) to unload data to S3, metadata from dynamoDB table
    arguments = getResolvedOptions(
        sys.argv,
        [
            'secret',
            'role_arn',
            'region_name',
            'dynamodb_table_name',
            'redshift_schema'
        ]
    )
    main(arguments)
