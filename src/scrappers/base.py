import os, sys
import regex as re
import logging, requests
from pathlib import Path
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from abc import ABC, abstractmethod

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.storage import MetadataDB

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    
    def __init__(self, search_title):
        self.site_name = "UnknownSite"
        self.search_title = search_title
        self.session = self.__request_session()
        self.url_id = None
        self.title = None
        self.id = None
        self.db = MetadataDB()
    
    @property
    def folder_name(self):
        if not self.title:
            return "Unknown_Title"
        
        clean = re.sub(r'[^a-zA-Z0-9 ]', '', self.title)
        return (clean[:60].strip()) if len(clean) > 60 else clean
    
    @property
    def main_folder(self):
        return Path("Media") / Path(self.site_name) / self.folder_name
    
    def __request_session(self):
        
        session = requests.Session()
        
        retry_strategy = Retry(
            total=5,
            backoff_factor=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    @abstractmethod
    def _get_id(self):
        pass
    
    @abstractmethod
    def get_chapters(self):
        pass
    
    @abstractmethod
    def download(self):
        pass