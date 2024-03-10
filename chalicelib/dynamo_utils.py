import boto3
import json
from datetime import datetime, timedelta
from loguru import logger


# Create a DynamoDB client
dynamodb = boto3.client('dynamodb')
table_name = 'chat-context-table'


def create_chat_context_table():
    # Read the JSON configuration file
    with open('dynamodb_config.json') as f:
        dynamodb_config = json.load(f)
    # Create the table using the configuration file
    return dynamodb.create_table(**dynamodb_config)


def read_by_chat_id(chat_id):
    table = dynamodb.Table(table_name)
    response = table.query(
        KeyConditionExpression=Key('chat_id').eq(chat_id)
    )
    # parsed_response = json.loads(response)
    logger.info(f"There are {response['Count']} rows for {chat_id}.")
    messages = [item['message'] for item in response['Items']]
    logger.info(f"Messages: \r{messages}")
    return messages


def save(chat_id, message, is_user):
    role = 'user' if is_user else 'assistant'
    item = {
        'chat_id': chat_id,
        'role': role,
        'message': message,
        'ttl': int((datetime.now() + timedelta(hours=1)).timestamp())
    }

    table = dynamodb.Table(table_name)
    table.put_item(Item=item)
    logger.info(f"Records has been saved")
