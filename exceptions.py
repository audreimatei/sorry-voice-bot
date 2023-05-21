class BigFileError(Exception):
    """Appear if the received file is larger than MAX_FILESIZE_DOWNLOAD."""


class InvalidFiletypeError(Exception):
    """Appear if the received filetype is invalid."""


class NoneFileSizeError(Exception):
    """Appear if the file size is None."""


class EmptyMessageError(Exception):
    """Appear if the message is empty."""


class EmptyTranscriptError(Exception):
    """Appear if the transcript is empty."""
