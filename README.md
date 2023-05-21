# sorry-voice-bot

Telegram-bot for audio and video transcribing.

## About models

- Transcribing model *vosk-model-small-ru-0.22* is preinstalled to *models/vosk/*. You can download other Vosk models from [here](https://alphacephei.com/vosk/models).

- Punctuation model is preinstalled to *models/silero/* from [here](https://github.com/snakers4/silero-models/).

## How to run the bot

Rename *.env.example* to *.env* and fill in the following variables:
- TELEGRAM_TOKEN — your Telegram-bot token. You can get it from BotFather.
- ENHANCE_TEXT_LANG — language of text enhancement. Can be 'en', 'de', 'ru', 'es'.

To run the bot in Docker:
```
$ docker-compose up
```

To run the bot in a virtual environment, first install ffmpeg from your preferred package manager or from the [ffmpeg website](https://ffmpeg.org/download.html) and then run the following commands:
```
$ python3.10 -m venv venv
$ . venv/bin/activate
$ pip install -U pip
$ pip install -r requirements.txt
$ venv/bin/python bot.py
```

## How to use

After launching the bot, go to Telegram and send */start* to the bot (whose token you put in TELEGRAM_TOKEN). The bot will welcome you. Next, send an audio, voice, video, or file. The bot will respond with a transcript.

## Contributing

Feel free to use Github Issues if you want to report bug, suggest improvements or anything else.