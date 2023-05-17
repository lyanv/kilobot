import asyncio
import logging
import os

import uvicorn as uvicorn
from quart import Quart, request
from telegram import Update

from settings import level

from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, CallbackQueryHandler, \
    ConversationHandler

from settings import TELEGRAM_API_KEY, DROP_DATA, ADMIN_ID, TG_READ_TIMEOUT
from bot.handlers import start, restart_bot, handle_model_choice, handle_message, show_all_data, data, start_drop, \
    drop_data
from bot.request_handlers import handle_request, request_access

app = Quart(__name__)

logging.basicConfig(level=level)


async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_API_KEY).read_timeout(TG_READ_TIMEOUT).build()
    application.add_handler(CommandHandler('Start', start))
    application.add_handler(CallbackQueryHandler(request_access, pattern="^request_access$"))
    application.add_handler(CallbackQueryHandler(handle_request, pattern="^(standard|reduced|unlimited|rejected):"))
    application.add_handler(CallbackQueryHandler(handle_model_choice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Regex("^Перезапустить бота$"), restart_bot))
    application.add_handler(CommandHandler('data', data))
    application.add_handler(CallbackQueryHandler(show_all_data, pattern="^show_all_data$"))
    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(start_drop, pattern="^start_drop$")],
            states={
                DROP_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, drop_data)],
            },
            fallbacks=[],
            allow_reentry=True
        ))
    application.bot_data["admin_id"] = ADMIN_ID

    @app.route('/telegram', methods=['POST'])
    async def webhook():
        if request.method == "POST":
            await application.update_queue.put(
                Update.de_json(data=await request.get_json(), bot=application.bot)
            )
            return '', 200

    port = int(os.getenv("PORT", 8000))

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=app,
            port=port,
            use_colors=False,
            host="0.0.0.0",
        )
    )

    @app.route('/', methods=['GET'])
    async def home():
        return 'Hello, world!', 200

    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == '__main__':
    asyncio.run(main())
