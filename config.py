"""
Configuration management for API keys and application settings.

Handles environment variables and provides default configurations
following the fail-fast principle with clear error messages.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def get_api_key(service: str) -> str:
    """
    Get API key for specified service.
    
    Args:
        service: Service name ('alpha_vantage' or 'openrouter')
        
    Returns:
        API key string
        
    Raises:
        ConfigError: If API key is not found or empty
    """
    key_mapping = {
        'alpha_vantage': 'ALPHA_VANTAGE_API_KEY',
        'openrouter': 'OPENROUTER_API_KEY'
    }
    
    if service not in key_mapping:
        raise ConfigError(f"Unknown service: {service}")
    
    env_var = key_mapping[service]
    api_key = os.getenv(env_var)
    
    if not api_key:
        raise ConfigError(f"Missing {env_var} in environment variables")
    
    return api_key


def get_database_path() -> str:
    """Get SQLite database file path."""
    return os.getenv('DATABASE_PATH', 'trading_journal.db')


def get_api_timeout() -> int:
    """Get API request timeout in seconds."""
    timeout_str = os.getenv('API_TIMEOUT', '30')
    try:
        return int(timeout_str)
    except ValueError:
        raise ConfigError(f"Invalid API_TIMEOUT value: {timeout_str}")


def get_supported_symbols() -> list[str]:
    """Get list of supported stock symbols."""
    symbols_str = os.getenv('SUPPORTED_SYMBOLS', 'NVDA,TSLA,HOOD,CRCL')
    return [symbol.strip().upper() for symbol in symbols_str.split(',')]


def validate_config() -> None:
    """
    Validate all required configuration.
    
    Raises:
        ConfigError: If any required configuration is missing or invalid
    """
    # Validate API keys (will raise ConfigError if missing)
    get_api_key('alpha_vantage')
    get_api_key('openrouter')
    
    # Validate other settings
    get_api_timeout()
    symbols = get_supported_symbols()
    
    if not symbols:
        raise ConfigError("No supported symbols configured")