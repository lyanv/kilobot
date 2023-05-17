from google.cloud import firestore
import logging

from telegram.ext import CallbackContext

db = firestore.AsyncClient()


async def clear_context_db(user_id):
    try:
        await db.collection('users').document(str(user_id)).update({
            'context': firestore.DELETE_FIELD
        })
    except Exception as e:
        logging.info(f"Ошибка при очистке контекста в базе данных: {e}")


async def set_context_to_db(user_id, doc_data: dict):
    try:
        data = {"context": doc_data}
        await db.collection('users').document(str(user_id)).set(data, merge=True)
    except Exception as e:
        logging.info(f"Ошибка при сохранении контекста в базе данных: {e}")


async def get_context_data_from_db(user_id, key):
    try:
        data = await db.collection('users').document(str(user_id)).get()
        context = data.to_dict().get("context")
        if context:
            return context.get(key)
        return None
    except Exception as e:
        logging.info(f"Ошибка при получении данных контекста из базы данных: {e}")
        return None


async def get_context_from_db(user_id):
    try:
        data = await db.collection('users').document(str(user_id)).get()
        context = data.to_dict().get("context")
        if not context:
            return None
    except Exception as e:
        logging.info(f"Ошибка при получении данных контекста из базы данных: {e}")
        return None


async def get_context_from_multiple(user_id, context: CallbackContext):
    data = context.user_data
    if data:
        return data
    return await get_context_from_db(user_id)


async def get_context_data_from_multiple(user_id, key, context: CallbackContext):
    data = context.user_data.get(key)
    if data:
        return data
    return await get_context_data_from_db(user_id, key)
