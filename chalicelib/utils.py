import openai

from functools import wraps
from loguru import logger
from telegram import ChatAction, ParseMode

me = 0  # me

allowed_ids = []


def reply(text, chat_id, context):
    context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )


def authorize(func):
    """
    Decorator function to send typing action to chat and check authorization.

    Parameters:
    func (function): the function to be decorated

    Returns:
    function: decorated function with typing action and authorization checks
    """
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        chat_id = update.effective_message.chat_id

        # Check if chat_id is allowed to run the command
        if chat_id in allowed_ids:
            # Send typing action to show the bot is processing
            context.bot.send_chat_action(
                chat_id=chat_id, action=ChatAction.TYPING)
            # Call the command function
            return func(update, context, *args, **kwargs)
        else:
            # Notify admin about unauthorized request
            reply(f'Unauthorised request from {chat_id}', me, context)
            logger.warning(f'Unauthorised request from {chat_id}')
            return None

    return command_func


def request_chatgpt(text, temperature, max_tokens, top_p, frequency_penalty, presence_penalty):
    logger.info(text)
    message = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,

        messages=[
            {
                "role": "assistant",
                "content": text,
            },
        ]
    )
    # logger.info(message)
    return message["choices"][0]["message"]["content"]
