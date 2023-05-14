import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from settings import MODELS, level, handler

logger_keyboard = logging.getLogger()
logger_keyboard.setLevel(level)
logger_keyboard.addHandler(handler)

def get_request_access_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Подать заявку", callback_data="request_access")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_restart_keyboard():
    keyboard = [[KeyboardButton("Перезапустить бота")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, selective=True)


def get_model_choice_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(MODELS[0], callback_data=MODELS[0]),
            InlineKeyboardButton(MODELS[1], callback_data=MODELS[1])
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_approve_keyboard(user_id, user_name, user_fullname):
    keyboard = [
        [
            InlineKeyboardButton("Standard", callback_data=f"standard:{user_id}:{user_name}:{user_fullname}"),
            InlineKeyboardButton("Reduced", callback_data=f"reduced:{user_id}:{user_name}:{user_fullname}"),
            InlineKeyboardButton("Unlimited", callback_data=f"unlimited:{user_id}:{user_name}:{user_fullname}")
        ],
        [
            InlineKeyboardButton("Rejected", callback_data=f"rejected:{user_id}:{user_name}:{user_fullname}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_db_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Показать все данные", callback_data="show_all_data"),
            InlineKeyboardButton("Удалить", callback_data="start_drop")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
