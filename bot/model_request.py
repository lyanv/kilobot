import re

import httpx
from telegram.constants import ParseMode


from bot.keyboard import get_restart_keyboard
from settings import OPENAI_API_KEY, DEFAULT_GPT_TIMEOUT, DEFAULT_GPT_TOKENS
from storage.database import get_context_data_from_multiple


# TODO: написать обработчика накопления контекста (лимит контекста)
async def gpt_request(update, context) -> None:
    user_message = update.message.text
    user_id = update.effective_chat.id

    if 'messages' not in context.user_data:
        context.user_data['messages'] = [
            {"role": "system", "content": "ИИ-ассистент"}
        ]

    context.user_data['messages'].append({"role": "user", "content": user_message})

    async with httpx.AsyncClient(timeout=DEFAULT_GPT_TIMEOUT) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            },
            json={
                "model": await get_context_data_from_multiple(user_id, 'selected_model', context),
                "messages": context.user_data['messages'],
                "max_tokens": DEFAULT_GPT_TOKENS,
                "temperature": 0.7,
            },
        )
    if 'choices' in response.json() and response.json()['choices']:
        resp = response.json()['choices'][0]['message']['content']
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ошибка запроса в OpenAI."
        )
        from bot.handlers import restart_bot
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

    context.user_data['messages'].append({"role": "assistant", "content": resp})
