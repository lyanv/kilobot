
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, CallbackQueryHandler, \
    ConversationHandler

from settings import TELEGRAM_API_KEY, DROP_DATA, ADMIN_ID
from .handlers import start, restart_bot, handle_model_choice, handle_message, show_all_data, data, start_drop, \
    drop_data
from .request_handlers import handle_request, request_access

application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
application.bot_data["admin_id"] = ADMIN_ID
application.add_handler(CommandHandler('Start', start))
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

application.add_handler(CallbackQueryHandler(request_access, pattern="^request_access$"))
application.add_handler(CallbackQueryHandler(handle_request, pattern="^(standard|reduced|unlimited|rejected):"))
application.add_handler(CallbackQueryHandler(handle_model_choice))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))