from telegram import Message


async def send_error_message(
    message: Message,
    error_text: str
) -> None:
    """Send error message to user."""

    await message.reply_text(error_text)
