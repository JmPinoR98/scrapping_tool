# main.py
import os, sys, json
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


from src.scrappers import MangaDexScraper

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
        print("3. Exit")
        choice = input("Select an option: ")
        
        if choice == "1":
            print("Manga Menu:")
            print("1. Write a Manga")
            print("2. List")
            choice = input("Select an option: ")
            
            if choice == "1":
                manga_name = input("Write Manga name: ")
                manga = MangaDexScraper(manga_name)
                manga.download()

            elif choice == "2":
                manga_list = [
                    "Isekai demo Bunan ni Ikitai Shoukougun",
                    "Yasei no Last Boss ga Arawareta!",
                    "Garbage Brave: Isekai ni Shoukan Sare Suterareta Yuusha no Fukushuu Monogatari",
                    "Henkyou-gurashi no Maou, Tensei Shite Saikyou no Majutsushi ni Naru",
                    "Akuyaku Onzoushi no Kanchigai Seija Seikatsu ~Nidome no Jinsei wa Yaritai Houdai Shitai Dake na no ni~",
                    "Tenkuu no Shiro wo Moratta node Isekai de Tanoshiku Asobitai",
                    "Magi Craft Meister",
                    'Isekai de "Kuro no Iyashi Te" tte Yobareteimasu',
                    "Manadeshi ni Uragirarete Shinda Ossan Yuusha, Shijou Saikyou no Maou to Shite Ikikaeru",
                    "Zense wa Kentei. Konjou Kuzu Ouji",
                    "Maou ni Natta node, Dungeon Tsukutte Jingai Musume to Honobono Suru",
                    "Tondemo Skill de Isekai Hourou Meshi",
                    "The New Gate",
                    "Kuro no Shoukanshi",
                    "Isekai Nonbiri Nouka",
                    "Genjitsushugi Yuusha no Oukoku Saikenki",
                    "Hokuo Kizoku to Moukinzuma no Yukiguni Karigurashi",
                    "Acchi Kocchi",
                    "Onna Doushi toka Arienai desho to Iiharu Onnanoko wo, Hyakunichikan de Tetteiteki ni Otosu Yuri no Ohanashi",
                    "Ookami no Kawa o Kabutta Hitsujihime",
                    'Hazure Skill "Kage ga Usui" o Motsu Guild Shokuin ga, Jitsu wa Densetsu no Ansatsusha',
                    "Tensei Oujo to Tensai Reijou no Mahou Kakumei",
                    "Henkyou Mobu Kizoku no Uchi ni Totsuidekita Akuyaku Reijou ga, Mechakucha Dekiru Ii Yome nandaga?",
                    "Futago no Ane ga Miko to shite Hikitorarete, Watashi wa Suterareta kedo Tabun Watashi ga Miko de aru.",
                    "Dig It"
                ]
                
                if not manga_list:
                    print("There is no mangas in the list")
                
                for manga_name in manga_list:
                    manga = MangaDexScraper(manga_name)
                    if manga.chapters:
                        manga.download()
            else:
                print("Invalid choice. Select only the valid options.")
            
        elif choice == "2":
            # novel = Novel("Lord of the Mysteries")
            # novel.download_text()
            print("Novel scraper not yet implemented.")
        
        elif choice == "3":
            sys.exit("Exit application")
        
        else:
            print("Invalid choice. Select only the valid options.")