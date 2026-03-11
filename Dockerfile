FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV SONG_GENIE_FLASK_HOST=0.0.0.0
ENV SONG_GENIE_FLASK_PORT=5000
ENV SONG_GENIE_FLASK_DEBUG=false

CMD ["python", "app.py"]

