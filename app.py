import os
import json
import traceback
# import boto3

from loguru import logger
from chalice import Chalice
from telegram.ext import (
    CommandHandler,
    Dispatcher,
    MessageHandler,
    Filters,
)
from telegram import Update, Bot

# from chalicelib.dynamo_utils import create_chat_context_table, read_by_chat_id, save
from chalicelib.utils import me, authorize, reply, request_chatgpt

# Telegram token
TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Chalice Lambda app
APP_NAME = "chatgpt-telegram-bot"
MESSAGE_HANDLER_LAMBDA = "message-handler-lambda"

app = Chalice(app_name=APP_NAME)
app.debug = True

# Telegram bot
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)


# This function will be called every time the Lambda function is deployed
# @app.on_deploy(stage='dev')
# def create_table():
#     response = create_chat_context_table()
#     logger.info('!!!Table has been created!!!')
#     logger.info(response)


def ask_chatgpt(
    text: str,
    temperature: float = 0.5,
    max_tokens: int = 3000,
    top_p: float = 1,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
) -> str:
    """
    Args:
        text: The input text for which to generate a response.
        temperature: degree of randomness in generated text. Default: 0.5
        max_tokens: max number of tokens in generated text. Default: 3000
        top_p: proportion of probability mass given to top tokens. Default: 1
        frequency_penalty: penalizes generator for repeating same word. Default: 0.0
        presence_penalty: penalizes generator for generating words not in input. Default: 0.0
    Returns:
        str: The generated response to the input text.
    """
    try:
        message = request_chatgpt(text, temperature, max_tokens, top_p,
                                  frequency_penalty, presence_penalty)
    except Exception as e:
        logger.error()
        app.log.error(traceback.format_exc())
        return f'Error:\n{e}'
    else:
        return message

#####################
# Telegram Handlers #
#####################


@authorize
def ask(update, context):
    chat_id = update.message.chat_id
    text = update.message.text
    # previous_messages = read_by_chat_id(chat_id)
    response = ask_chatgpt(text, temperature=0.1)
    # save(chat_id, text, is_user=True)
    # save(chat_id, response, is_user=False)
    reply(response, chat_id, context)


def ping(update, context):
    chat_id = update.message.chat_id
    user_id = update.to_dict()['message']['from']['id']
    message = f'ChatId: {chat_id}\nFromId: {user_id}'
    reply(message, me, context)


@authorize
def admin(update, context):
    chat_id = update.message.chat_id
    user_id = update.to_dict()['message']['from']['id']

    if user_id in [me]:
        reply('You are admin', chat_id, context)
    else:
        reply(f'Not enough permissions to run this command.', chat_id, context)


def error_handler(update, context):
    logger.warning('ErrorHandler invoked')
    chat_id = update.message.chat_id
    reply(f'Error: {context.error}\n\n{update}', chat_id, context)


############################
# Lambda Handler functions #
############################

@app.lambda_function(name=MESSAGE_HANDLER_LAMBDA)
def message_handler(event, context):
    dispatcher.add_handler(CommandHandler('ping', ping))
    dispatcher.add_handler(CommandHandler('admin', admin))

    dispatcher.add_handler(MessageHandler(Filters.text, ask))
    dispatcher.add_error_handler(error_handler)

    try:
        dispatcher.process_update(
            Update.de_json(json.loads(event["body"]), bot))
    except Exception as e:
        print(e)
        return {"statusCode": 500}

    return {"statusCode": 200}
