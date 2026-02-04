import logging

import socials.discord as discord


class DiscordHandler(logging.Handler):
    """
    Custom logging handler that sends records to a Discord webhook.
    """

    def __init__(self, config, role_id=None):
        super().__init__()
        self.config = config
        self.role_id = role_id

    def emit(self, record):
        if not self.config.getboolean("DISCORD", "ENABLE"):
            return

        try:
            log_entry = self.format(record)

            if len(log_entry) > 1900:
                log_entry = (
                    log_entry[:100] + "\n... [TRUNCATED] ...\n" + log_entry[-1800:]
                )

            discord.post(
                log_entry,
                self.config.get("DISCORD", "STATUS_URL"),
                role_id=self.role_id,
            )
        except Exception:
            self.handleError(record)


def setup_logging(config, debug=False):
    """
    Configures the root logger with console and Discord handlers.
    """
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Common Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Discord Status Handler
    # Only add if Discord is enabled
    if config.has_section("DISCORD") and config.getboolean("DISCORD", "ENABLE"):
        role_id = (
            config.get("DISCORD", "ROLE_ID")
            if config.has_option("DISCORD", "ROLE_ID")
            and config.get("DISCORD", "ROLE_ID").strip() != ""
            else None
        )
        discord_handler = DiscordHandler(config, role_id=role_id)

        discord_handler.setLevel(logging.WARNING)

        discord_formatter = logging.Formatter("%(levelname)s: %(message)s")
        discord_handler.setFormatter(discord_formatter)
        logger.addHandler(discord_handler)

    return logger
