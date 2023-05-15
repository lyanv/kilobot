from telegram import Update
from telegram.ext import CallbackContext

from settings import ADMIN_ID
from .keyboard import get_approve_keyboard
from .limits import set_user_limits, get_user_info


async def request_access(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_name = update.effective_user.name
    user_fullname = update.effective_user.full_name
    context.user_data['status'] = 'pending'
    await update.callback_query.edit_message_text("Заявка на рассмотрении.")
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Заявка от {user_name} (ID: {user_id}, FullName: {user_fullname}). Выберите доступ:",
        reply_markup=get_approve_keyboard(user_id, user_name, user_fullname)
    )


async def handle_request(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(":")
    action, user_id, user_name, user_fullname = data[0], int(data[1]), data[2], data[3]

    answer = f"User_name: {user_name} (ID: {user_id}, FullName: {user_fullname}) Status: {action}."

    await set_user_limits(user_id, action, user_name, user_fullname)
    await query.message.reply_text(text=answer)
    user_info = await get_user_info(user_id)
    if action in ['standard', 'reduced']:
        text = f"""
Заявка одобрена
Дневной лимит: {user_info.get("limit_daily")} сообщений
Недельный лимит: {user_info.get("limit_weekly")} сообщений
"""
    elif action == 'unlimited':
        text = "Вам одобрен безлимитный доступ"
    else:
        text = "Заявка не одобрена"

    await context.bot.send_message(chat_id=user_id, text=text)
