import asyncio
import logging
import sys
from io import BytesIO
from tempfile import NamedTemporaryFile

import torch
import vosk
from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from constants import (AUDIO_CHANNELS, AUDIO_FORMAT, BIG_FILE_ERROR_TEXT,
                       EMPTY_MESSAGE_ERROR_TEXT, EMPTY_TRANSCRIPT_ERROR_TEXT,
                       ENHANCE_TEXT_LANGUAGE, GREET, LOG_CONVERTED,
                       LOG_DOWNLOADED, LOG_ENHANCED, LOG_GREET, LOG_RECOGNIZED,
                       LOG_TRANSCRIPT_SEND, MAX_FILESIZE_DOWNLOAD,
                       MAX_TEXT_LENGTH, NONE_FILE_SIZE_ERROR_TEXT,
                       NOT_VALID_FILETYPE_ERROR_TEXT, SAMPLE_RATE,
                       TELEGRAM_TOKEN)
from exceptions import (BigFileError, EmptyMessageError, EmptyTranscriptError,
                        InvalidFiletypeError, NoneFileSizeError)
from utils import send_error_message

vosk.SetLogLevel(-1)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


async def greet(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a welcome message."""

    if update.message is None:
        raise EmptyMessageError(EMPTY_MESSAGE_ERROR_TEXT)

    await update.message.reply_text(GREET)

    logger.debug(LOG_GREET)


async def download_file(message: Message) -> bytes:
    """Download file and return it."""

    file_type = (
        message.voice
        or message.video_note
        or message.audio
        or message.document
        or message.video
    )

    if file_type is None:
        await send_error_message(message, NOT_VALID_FILETYPE_ERROR_TEXT)
        raise InvalidFiletypeError(NOT_VALID_FILETYPE_ERROR_TEXT)

    if file_type.file_size is None:
        await send_error_message(message, NONE_FILE_SIZE_ERROR_TEXT)
        raise NoneFileSizeError(NONE_FILE_SIZE_ERROR_TEXT)

    if file_type.file_size > MAX_FILESIZE_DOWNLOAD:
        await send_error_message(message, BIG_FILE_ERROR_TEXT)
        raise BigFileError(BIG_FILE_ERROR_TEXT)

    with BytesIO() as bytefile_from_user:
        file_obj = await file_type.get_file()
        await file_obj.download_to_memory(bytefile_from_user)
        logger.debug(LOG_DOWNLOADED)
        bytefile_from_user.seek(0)
        return bytefile_from_user.read()


async def convert_file(bytefile_from_user: bytes) -> bytes:
    """Convert file to valid format and save to temporary file."""

    with NamedTemporaryFile() as tmpfile_in, \
         NamedTemporaryFile() as tmpfile_out:
        tmpfile_in.write(bytefile_from_user)
        process = await asyncio.create_subprocess_exec(
            'ffmpeg',
            '-loglevel', 'quiet',
            '-y',
            '-i', tmpfile_in.name,
            '-ac', str(AUDIO_CHANNELS),
            '-f', AUDIO_FORMAT,
            '-ar', str(SAMPLE_RATE),
            tmpfile_out.name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process.wait()

        logger.debug(LOG_CONVERTED)

        return tmpfile_out.read()


async def recognize_speech(speech: bytes) -> str:
    """Recognize text from audio using Vosk."""

    model = vosk.Model(model_path='models/vosk')
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.AcceptWaveform(speech)
    logger.debug(LOG_RECOGNIZED)
    return recognizer.FinalResult()[14:-3]


async def enhance_transcript(transcript: str) -> str:
    """Enhance recognized text using a Silero model."""

    te_model = torch.package.PackageImporter(
        file_or_buffer='models/silero/v2_4lang_q.pt'
    ).load_pickle(package='te_model', resource='model')
    logger.debug(LOG_ENHANCED)
    return te_model.enhance_text(transcript, ENHANCE_TEXT_LANGUAGE)


async def send_transcript(
    message: Message,
    transcript: str
) -> None:
    """Send transcript in chunks to Telegram chat."""

    for chunk_start in range(0, len(transcript), MAX_TEXT_LENGTH):
        await message.reply_text(
            transcript[chunk_start:chunk_start+MAX_TEXT_LENGTH]
        )


async def transcribe(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Convert and recognize file, enhance and send transcript."""

    if update.message is None:
        raise EmptyMessageError(EMPTY_MESSAGE_ERROR_TEXT)

    transcript = await recognize_speech(
        await convert_file(
            await download_file(update.message)))

    if not transcript:
        logger.error(EMPTY_TRANSCRIPT_ERROR_TEXT)
        send_error_message(update.message, EMPTY_TRANSCRIPT_ERROR_TEXT)
        raise EmptyTranscriptError(EMPTY_TRANSCRIPT_ERROR_TEXT)

    transcript = await enhance_transcript(transcript)

    await send_transcript(update.message, transcript)

    logger.debug(LOG_TRANSCRIPT_SEND)


def main() -> None:
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        application.add_handler(CommandHandler('start', greet))

        application.add_handler(
            MessageHandler(
                filters.VOICE | filters.Document.AUDIO | filters.AUDIO |
                filters.VIDEO_NOTE | filters.Document.VIDEO | filters.VIDEO,
                transcribe
            )
        )

        application.run_polling()

    except TelegramError as error:
        logger.error(f'Failed to send a message to Telegram: {error}')

    except (
        BigFileError,
        EmptyMessageError,
        EmptyTranscriptError,
        InvalidFiletypeError,
        NoneFileSizeError
    ) as error:
        logger.error(str(error))

    except Exception as error:
        logger.exception(f'Unexpected error: {error}')


if __name__ == '__main__':
    main()
