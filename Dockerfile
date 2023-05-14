FROM python:3.9

WORKDIR /app
ADD . /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY chatbots-383016-e4fda5d3fbe6.json /app/chatbots-383016-e4fda5d3fbe6.json
COPY .env .env
ENV QUART_APP=app.py
CMD ["sh", "-c", "hypercorn app:app -b 0.0.0.0:${PORT:-8080}"]
