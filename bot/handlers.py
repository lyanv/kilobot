import json
from datetime import timedelta, datetime

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from settings import REJECT_COOLING_PERIOD_DAYS, REQUEST_COOLING_PERIOD_SEC, DROP_DATA, tz
from storage.database import db, clear_context_db, set_context_to_db, get_context_data_from_multiple
from .keyboard import get_model_choice_keyboard, get_restart_keyboard, get_request_access_keyboard, get_db_keyboard
from .limits import cooldown, get_user_info, check_limits, update_request_data
from .model_request import gpt_request


async def restart_bot(update: Update, context: CallbackContext):
    await start(update, context)


async def data(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if str(user_id) != context.bot_data['admin_id']:
        await update.message.reply_text("Доступно только админу")
        return

    await update.message.reply_text(text="Действия с базой", reply_markup=get_db_keyboard())


async def show_all_data(update: Update, context: CallbackContext) -> None:
    docs = db.collection('users').stream()
    async for doc in docs:
        doc_data = doc.to_dict()
        doc_text = json.dumps(doc_data, indent=4, ensure_ascii=False)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=doc_text
        )


async def start_drop(update: Update, context: CallbackContext) -> int:
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Укажите user_id для удаления.')
    return DROP_DATA


async def drop_data(update: Update) -> int:
    user_id_to_drop = update.message.text
    doc_ref = db.collection('users').document(user_id_to_drop)

    doc = await doc_ref.get()
    if doc.exists:
        await doc_ref.delete()
        await update.message.reply_text(f'Пользователь {user_id_to_drop} удален')
    else:
        await update.message.reply_text(f'Пользователь {user_id_to_drop} не найден')
    return ConversationHandler.END


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_chat.id

    context.user_data.clear()
    await clear_context_db(user_id)

    db_user_data = await get_user_info(user_id)

    if db_user_data is None or 'status' not in db_user_data:
        answer = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Подайте заявку на доступ.",
            reply_markup=get_request_access_keyboard()
        )

    elif db_user_data['status'] == 'rejected':
        action_ts = tz.localize(datetime.strptime(db_user_data['action_ts'], "%Y-%m-%d %H:%M:%S"))
        time_since_rejection = datetime.now(tz) - action_ts
        if time_since_rejection >= timedelta(days=REJECT_COOLING_PERIOD_DAYS):
            answer = context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Подайте повторную заявку на доступ.",
                reply_markup=get_request_access_keyboard()
            )
        else:
            reject_time = action_ts.strftime("%Y-%m-%d %H:%M:%S")
            answer = context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Ваша заявка была отклонена {reject_time}. Новая заявка через {REJECT_COOLING_PERIOD_DAYS} суток",
                reply_markup=get_restart_keyboard()
            )

    else:
        answer = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Выберите модель:",
            reply_markup=get_model_choice_keyboard()
        )
    await answer


async def handle_model_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    context.user_data['selected_model'] = query.data

    await set_context_to_db(user_id=update.effective_chat.id, doc_data={'selected_model': query.data})
    await query.answer()
    await query.edit_message_text(text=f"Спросите что-нибудь у {query.data}.")


async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if cooldown(user_id) & (str(user_id) != context.bot_data['admin_id']):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Интервал между запросами {REQUEST_COOLING_PERIOD_SEC} секунд.",
            reply_markup=get_restart_keyboard()
        )
        return

    db_user_data = await get_user_info(user_id)

    error_message = await check_limits(user_id, db_user_data)
    if error_message:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)
        await restart_bot(update, context)
        return

    sm_in_context = await get_context_data_from_multiple(user_id, 'selected_model', context)

    if not sm_in_context:
        await restart_bot(update, context)
        return

    await gpt_request(update, context)
    await update_request_data(user_id)
