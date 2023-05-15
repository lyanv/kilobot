import logging

from quart import Quart, request
from telegram import Update

from bot.bot import application
from settings import PORT, WEBHOOKURL, level

app = Quart(__name__)

logging.basicConfig(level=level)


@app.route('/setwebhook', methods=['GET', 'POST'])
async def set_webhook():
    s = await application.bot.set_webhook(url=f"{WEBHOOKURL}/telegram")
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/telegram', methods=['POST'])
async def webhook():
    if request.method == "POST":
        req_data = await request.get_json(force=True)
        update = Update.de_json(req_data, application.bot)
        async with application:
            await application.process_update(update)
        return '', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
