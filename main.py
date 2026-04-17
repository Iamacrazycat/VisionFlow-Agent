from src.utils import setup_logging
from src.bot import AutoRocoBot

def main() -> None:
    # Setup global logging
    setup_logging()
    
    # Initialize and run bot
    bot = AutoRocoBot()
    bot.prompt_mode()
    bot.run()

if __name__ == "__main__":
    main()
