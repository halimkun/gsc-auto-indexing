"""
Configuration loader for GSC Auto Submit.

Reads config.conf and provides access to Google credentials.

Author: halimkun (https://github.com/halimkun)
"""

import configparser
import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config.conf"


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> configparser.ConfigParser:
    """Load and return the configuration from config.conf."""
    config = configparser.ConfigParser()

    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        logger.info("Please copy config.conf.example to config.conf and fill in your credentials")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config.read(config_path)
    logger.info(f"Config loaded from: {config_path}")
    return config


def get_service_account_path(config: configparser.ConfigParser) -> str:
    """Extract the service account file path from config."""
    try:
        path = config.get("google", "service_account_file")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logger.error(f"Missing config key: {e}")
        raise ValueError(f"Missing required config: [google] service_account_file") from e

    if not os.path.exists(path):
        logger.error(f"Service account file not found: {path}")
        raise FileNotFoundError(f"Service account file not found: {path}")

    logger.info(f"Service account file: {path}")
    return path
