import re

import httpx
from telegram.constants import ParseMode

from bot.keyboard import get_restart_keyboard
from settings import OPENAI_API_KEY, DEFAULT_GPT_TIMEOUT, DEFAULT_GPT_TOKENS


async def gpt_request(update, context) -> None:
    user_message = update.message.text

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
                "model": context.user_data['selected_model'],
                "messages": context.user_data['messages'],
                "max_tokens": DEFAULT_GPT_TOKENS,
                "temperature": 0.7,
            },
        )
    resp = response.json()['choices'][0]['message']['content']

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
