FROM python:3.10-slim as build

RUN python -m venv /app
RUN /app/bin/pip install -U pip

COPY requirements.txt .
RUN /app/bin/pip install -r requirements.txt


FROM python:3.10-slim

RUN apt update && apt install -y ffmpeg

WORKDIR /app

COPY --from=build /app /app
COPY . .

CMD /app/bin/python bot.py
