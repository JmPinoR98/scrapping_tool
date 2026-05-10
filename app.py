# main.py
import os, sys, json
import logging,argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.classes import Manga

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "file": record.filename,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

def setup_logging():

    log_dir = os.path.join(current_dir, "src", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "logging.json")
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter(datefmt='%Y-%m-%dT%H:%M:%S'))
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    text_formatter = logging.Formatter('[%(asctime)s] - [%(levelname)s] - %(name)s - %(message)s', '%I:%M:%S %p')
    console_handler.setFormatter(text_formatter)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, console_handler]
    )

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    
    while True:
        print("\nWelcome to the Universal Scraper!")
        print("1. Download Manga")
        print("2. Download Novel")
        
        choice = input("Select an option (1/2): ")
        
        if choice == "1":
            print("Manga Menu:")
            print("1. Write a Manga")
            print("2. List")
            choice = input("Select an option (1/2): ")
            
            if choice == "1":
                manga_name = input("Write Manga name: ")
                manga = Manga(manga_name)
                manga.download()

            elif choice == "2":
                manga_list = [
                    # "Please Bully Me, Miss Villainess!",
                    "Goshujinsama to Yuku Isekai Survival!",
                    "sekai Shounin - Skill <Isekai Tokou> wo Kushi Shite, Yuuyuu Jiteki na Okanemochi Slow Life wo Okurimasu",
                    "Tsuki ga Michibiku Isekai Douchuu",
                    "Netachara-Tensei Toka Anmarida!"
                ]
                
                if not manga_list:
                    print("There is no mangas in the list")
                
                for manga_name in manga_list:
                    manga = Manga(manga_name)
                    manga.download()

            else:
                print("Invalid choice. Select only the valid options.")
            
        elif choice == "2":
            # novel = Novel("Lord of the Mysteries")
            # novel.download_text()
            print("Novel scraper not yet implemented.")
            
        else:
            print("Invalid choice. Select only the valid options.")