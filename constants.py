import os

from dotenv import load_dotenv

load_dotenv()

# AUDIO SETTINGS
AUDIO_CHANNELS = 1
AUDIO_FORMAT = 's16le'
SAMPLE_RATE = 16000

# TELEGRAM LIMITS
MAX_TEXT_LENGTH = 4096
MAX_FILESIZE_DOWNLOAD = int(20e6)

# ENV
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
ENHANCE_TEXT_LANGUAGE = os.getenv('ENHANCE_TEXT_LANGUAGE', '')

# ERROR TEXT
BIG_FILE_ERROR_TEXT = (
    'К сожалению, Telegram разрешает ботам скачивать'
    ' только файлы размером менее'
    f' {MAX_FILESIZE_DOWNLOAD} байт.'
)
EMPTY_MESSAGE_ERROR_TEXT = 'update.messagе is None.'
NOT_VALID_FILETYPE_ERROR_TEXT = 'Тип файла не поддерживается.'
NONE_FILE_SIZE_ERROR_TEXT = 'Файл пуст.'
EMPTY_TRANSCRIPT_ERROR_TEXT = 'Транскрипт пуст, ничего не распознано.'

# LOGGER
LOG_GREET = 'Bot sent a welcome message.'
LOG_DOWNLOADED = 'File downloaded to memory.'
LOG_CONVERTED = 'File converted to valid format.'
LOG_RECOGNIZED = 'Recognition complete.'
LOG_ENHANCED = 'Transcript enhancement complete.'
LOG_TRANSCRIPT_SEND = 'Bot sent transcript.'

GREET = (
    'Отправьте голосовое сообщение, видео или аудиофайл'
    'и бот отправит Вам транскрипцию.'
)
