# test_config.py
from utils.config_loader import ConfigLoader


def test_config():
    try:
        config = ConfigLoader.load_config()
        print("Configuration loaded successfully!")
        print("\nExchange Configuration:")
        print(f"API Key exists: {'api_key' in config['exchange']}")
        print(f"Secret Key exists: {'api_secret' in config['exchange']}")
        print("\nTelegram Configuration:")
        print(f"Bot Token exists: {'bot_token' in config['telegram']}")
        print(f"Chat ID exists: {'chat_id' in config['telegram']}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_config()