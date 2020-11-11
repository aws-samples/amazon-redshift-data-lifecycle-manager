from dataclasses import asdict

import boto3
import os
import csv
import codecs
import time

from validator import ConfigRecord

region = os.environ['AWS_REGION']
table_name = os.environ['TABLE_NAME']
rcu = os.environ['RCU']
wcu = os.environ['WCU']
bucket = os.environ['BUCKET']
key = os.environ['KEY']

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb', region_name=region)
dynamo_client = boto3.client('dynamodb', region_name=region)


def lambda_handler(event, context):
	try:
		obj = s3.Object(bucket, key).get()['Body']
	except Exception as e:
		return (
			f"S3 Object could not be opened. Check environment variable. "
			f"{e}"
		)
	batch = []
	# DictReader is a generator; not stored in memory
	for row in csv.DictReader(codecs.getreader('utf-8-sig')(obj)):
		if len(batch) >= 100:
			write_to_dynamo(batch)
			batch.clear()
		batch.append(row)
	if batch:
		print(f"Batch: {str(len(batch))}")
		write_to_dynamo(batch)

	return {
		"statusCode": 200,
		"body": "Uploaded to DynamoDB table"
	}


def write_to_dynamo(rows):
	# TODO: Validate each row before saving to DynamoDB
	try:
		with _get_table().batch_writer() as batch:
			for row in rows:
				batch.put_item(Item=asdict(ConfigRecord(**row)))
	except Exception as e:
		print(f"Error executing batch_writer: {str(e)}")


def _get_table():
	try:
		response = dynamo_client.describe_table(TableName=table_name)
	except dynamo_client.exceptions.ResourceNotFoundException:
		_create_table()
	return dynamodb.Table(table_name)
		
		
def _create_table():
	try:
		table = dynamodb.create_table(
			TableName=table_name,
			KeySchema=[
				{
					'AttributeName': 'schema_name',
					'KeyType': 'HASH'  # Partition key
				},
				{
					'AttributeName': 'table_name',
					'KeyType': 'RANGE'  # Sort key
				}
			],
			AttributeDefinitions=[
				{
					'AttributeName': 'schema_name',
					'AttributeType': 'S'
				},
				{
					'AttributeName': 'table_name',
					'AttributeType': 'S'
				}
			],
			ProvisionedThroughput={
				'ReadCapacityUnits': int(rcu),
				'WriteCapacityUnits': int(wcu)
			}
		)
		print(
			f'Creating DynamoDB table: '
			f'{table_name} with {rcu} RCUs and {wcu} WCUs'
		)
		# Check table status
		status = None
		while status != 'ACTIVE':
			time.sleep(3)
			response = dynamo_client.describe_table(TableName=table_name)
			status = str.upper(response['Table']['TableStatus'])
			print(f'Table status: {status}')
	except dynamo_client.exceptions.ResourceInUseException:
		print(f'Table: {table_name} already exists')
	return f'Table {table_name} created'
