FROM python:3.9

WORKDIR /app
ADD . /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY cbots-392507-6ec7ca6e9770.json /app/cbots-392507-6ec7ca6e9770.json
COPY .env .env
ENV QUART_APP=app.py
CMD ["python", "./app.py"]
