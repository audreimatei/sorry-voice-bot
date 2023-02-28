import logging
import os
import subprocess
import sys
from tempfile import NamedTemporaryFile

import torch
import vosk
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.constants import MAX_FILESIZE_DOWNLOAD, MAX_MESSAGE_LENGTH
from telegram.error import TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from telegram.ext.utils.types import CCT


from exceptions import BigFileError

load_dotenv()

vosk.SetLogLevel(-1)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

AUDIO_CHANNELS = 1
AUDIO_FORMAT = 's16le'
SAMPLE_RATE = 16000
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ENHANCE_TEXT_LANGUAGE = os.getenv(
    'ENHANCE_TEXT_LANGUAGE', default='en')


def greet(update: Update, context: CCT) -> None:
    """Send a welcome message."""
    try:
        if update.effective_chat:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=('Отправьте голосовое сообщение, видео или аудиофайл и'
                      ' бот отправит Вам транскрипцию.'),
                reply_to_message_id=update.message.message_id
            )
        else:
            logger.error('Update object does not contain effective chat.'
                         ' A welcome message not sent.')
    except TelegramError as error:
        logger.error(f'Telegram error while sending welcome message: {error}')
    except Exception as error:
        logger.exception(
            f'Unexpected error while sending welcome message: {error}')
        raise
    else:
        logger.debug('Bot sent a welcome message')


def download_file(update: Update, bot: Bot) -> bytes:
    """Download file and save to temporary file."""
    message_type = (update.message.voice or update.message.video_note
                    or update.message.audio or update.message.document
                    or update.message.video)
    if message_type.file_size > MAX_FILESIZE_DOWNLOAD:
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=('К сожалению, Telegram разрешает ботам скачивать'
                  ' только файлы размером менее'
                  f' {MAX_FILESIZE_DOWNLOAD} байт.'),
            reply_to_message_id=update.message.message_id
        )
        raise BigFileError(
            'The file is larger than MAX_FILESIZE_DOWNLOAD')
    with NamedTemporaryFile() as tmpfile:
        message_type.get_file().download(out=tmpfile)
        logger.debug('File downloaded to memory')
        tmpfile.seek(0)
        return tmpfile.read()


def convert_file(input_file: bytes) -> bytes:
    """Convert file to valid format and save to temporary file."""
    with NamedTemporaryFile() as tmpfile_out:
        try:
            subprocess.run(
                (
                    'ffmpeg',
                    '-loglevel', 'quiet',
                    '-y',
                    '-i', '-',
                    '-ac', str(AUDIO_CHANNELS),
                    '-f', AUDIO_FORMAT,
                    '-ar', str(SAMPLE_RATE),
                    tmpfile_out.name
                ),
                input=input_file,
                check=True
            )
            logger.debug('File converted to valid format')
        except subprocess.CalledProcessError as error:
            logger.exception(f'Error converting file: {error}')
            raise
        return tmpfile_out.read()


def recognize_speech(speech: bytes) -> str:
    """Recognize text from audio using Vosk."""
    model = vosk.Model(model_path='models/vosk')
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.AcceptWaveform(speech)
    logger.debug('Recognition complete')
    return recognizer.FinalResult()[14:-3]


def enhance_transcript(transcript: str) -> str:
    """Enhance recognized text using a Silero model."""
    te_model = torch.package.PackageImporter(
        file_or_buffer='models/silero/v2_4lang_q.pt'
    ).load_pickle(package='te_model', resource='model')
    logger.debug('Transcript enhancement complete')
    return te_model.enhance_text(transcript, ENHANCE_TEXT_LANGUAGE)


def send_transcript(transcript: str, update: Update, bot: Bot) -> None:
    """Send transcript in chunks to Telegram chat."""
    for chunk_start in range(0, len(transcript), MAX_MESSAGE_LENGTH):
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=transcript[chunk_start:chunk_start+MAX_MESSAGE_LENGTH],
            reply_to_message_id=update.message.message_id
        )


def transcribe(update: Update, context: CCT) -> None:
    """Convert and recognize file, enhance and send transcript."""
    try:
        transcript = recognize_speech(
            convert_file(download_file(update, context.bot)))
        if not transcript:
            logger.warning('Transcript is empty, nothing recognized')
            transcript = 'Не удалось ничего распознать'
        else:
            transcript = enhance_transcript(transcript)
        send_transcript(transcript, update, context.bot)
    except TelegramError as error:
        logger.error(f'Failed to send a message to Telegram: {error}')
    except Exception as error:
        logger.error(error)
    else:
        logger.debug('Bot sent transcript')


if __name__ == '__main__':
    try:
        updater = Updater(token=TELEGRAM_TOKEN)
        updater.dispatcher.add_handler(
            CommandHandler('start', greet, run_async=True))
        updater.dispatcher.add_handler(
            MessageHandler(
                Filters.voice | Filters.document.audio | Filters.audio |
                Filters.video_note | Filters.document.video | Filters.video,
                transcribe,
                run_async=True
            )
        )
        updater.start_polling()
        updater.idle()
    except TelegramError as error:
        logger.error(f'Failed to send a message to Telegram: {error}')
    except Exception as error:
        logger.error(error)
