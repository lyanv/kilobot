import re

import httpx
import json
from telegram.constants import ParseMode

from bot.keyboard import get_restart_keyboard
from settings import OPENAI_API_KEY, DEFAULT_GPT_TIMEOUT, DEFAULT_GPT_TOKENS
from storage.database import get_context_data_from_multiple
import base64


# TODO: написать обработчика накопления контекста (лимит контекста)
async def gpt_request(update, context) -> None:
    from bot.handlers import restart_bot


    user_id = update.effective_chat.id
    selected_model = await get_context_data_from_multiple(
        user_id, 'selected_model', context)

    models_dict = {
        'GPT-4-vision': 'gpt-4-vision-preview',
        'GPT-4-latest': 'gpt-4-1106-preview'
    }

    selected_model = models_dict[selected_model]

    is_vision_enabled = 'vision' in selected_model.lower()

    user_message = update.message.text or update.message.caption or "Пиши по-русски"

    new_user_message = {
        "role": "user",
        "content": [{"type": "text", "text": user_message}]
    }

    if update.message.photo and is_vision_enabled:
        pic = await update.message.photo[-2].get_file()
        new_user_message["content"].append(
            {"type": "image_url", "image_url": {"url": pic.file_path}}
        )

        if not update.message.caption:
            new_user_message["content"].append(
                {"type": "text", "text": "Что изображено"}
            )

    if 'messages' not in context.user_data:
        context.user_data['messages'] = [
            {"role": "system", "content": "ИИ-ассистент"},
            new_user_message
        ]
    else:
        context.user_data['messages'].append(new_user_message)

    # TODO upload multiple images


    import logging
    logging.info(context.user_data['messages'])

    async with httpx.AsyncClient(timeout=DEFAULT_GPT_TIMEOUT) as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json={
                    "model": selected_model,
                    "messages": context.user_data['messages'],
                    "max_tokens": DEFAULT_GPT_TOKENS,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Ошибка HTTP при запросе в OpenAI: {e.response.status_code}"
            )
            await restart_bot(update, context)
            return
        except httpx.RequestError as e:

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла сетевая ошибка при запросе в OpenAI."
            )
            await restart_bot(update, context)
            return
        except Exception as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла неизвестная ошибка."
            )
            await restart_bot(update, context)
            return
    try:

        if 'choices' in response.json() and response.json()['choices']:
            resp = response.json()['choices'][0]['message']['content']
        else:
            await restart_bot(update, context)
            return
    except json.JSONDecodeError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ошибка обработки ответа от OpenAI."
        )
        await restart_bot(update, context)
        return

    numtokens_out = response.json()['usage']['prompt_tokens']
    numtokens_in = response.json()['usage']['completion_tokens']

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Длина запроса: {numtokens_out} токенов\nДлина ответа: {numtokens_in} токенов")

    split_messages = re.split(r'(```.*?```)', resp, flags=re.DOTALL)

    for msg in split_messages:
        if msg.strip().startswith("`"):
            mode = ParseMode.MARKDOWN_V2
        else:
            mode = None

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=msg,
                                       reply_markup=get_restart_keyboard(),
                                       parse_mode=mode)

    context.user_data['messages'].append(
        {"role": "assistant", "content": resp})
