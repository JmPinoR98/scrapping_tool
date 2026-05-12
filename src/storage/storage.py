import sqlite3, logging

logger = logging.getLogger(__name__)

class MetadataDB:
    
    def __init__(self, db_path = 'metadata.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.__create_table()
        
    def __create_table(self):
        
        logging.debug("Start of creation of Database")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraped_media (
                id INTEGER PRIMARY KEY,
                url_id TEXT UNIQUE,
                site_id TEXT DEFAULT NULL,
                searched_name TEXT,
                saved_name TEXT,
                last_chapter_scraped INTEGER,
                sub_chapter INTEGER,
                media_type TEXT,
                insert_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logging.debug("End of creation of Database")

    def save_metadata(self, url_id, site_id, searched_name, saved_name, last_chapter, sub_chapter, media_type='manga'):
        logging.info("Start of metadata ingestion")
        self.cursor.execute('''
            INSERT INTO scraped_media (url_id, site_id, searched_name, saved_name, last_chapter_scraped, sub_chapter, media_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url_id) DO UPDATE SET
                last_chapter_scraped = excluded.last_chapter_scraped,
                sub_chapter = excluded.sub_chapter,
                update_date = CURRENT_TIMESTAMP
        ''', (url_id, site_id, searched_name, saved_name, last_chapter, sub_chapter, media_type))
        self.conn.commit()
        logging.info("End of metadata ingestion")
    
    def get_last_chapter(self, url_id):
        logging.info("Start of colecting last chapter in metadata")
        self.cursor.execute(f"SELECT last_chapter_scraped, sub_chapter FROM scraped_media WHERE url_id = ?", (url_id,))
        result = self.cursor.fetchone()
        logging.info("End of colecting last chapter in metadata")
        return (result[0], result[1]) if result else (0,0)
    
    def close(self):
        logging.info("Closing Connection with Database")
        self.conn.close()