import shutil
import logging
import os, sys, time
from collections import defaultdict

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from .base import BaseScraper
from utils.constants import BASE_URL, LANGUAGES, scanlation_groups

logger = logging.getLogger(__name__)

class MangaDexScraper(BaseScraper):
    
    def __init__(self, search_title):
        super().__init__(search_title)
        self.site_name = "MangaDex"
        self.id, self.title = self._get_id()
        self.url_id = f'https://www.mangadex.org/title/{self.id}'
        self.chapters = self.get_chapters()
    
    def _get_id(self):
        logger.info(f"Start of getting the ID of the manga: {self.search_title}")
        
        params = {
            "title": self.search_title,
            "order[relevance]": "desc",
            "contentRating[]": ["safe", "suggestive","erotica"], 
            "limit": 10
        }
        
        logger.debug(f"Manga Request URL: {BASE_URL}/manga. Params: {params}")
        r_manga = self.session.get(f"{BASE_URL}/manga", params=params)
        
        data = r_manga.json().get("data", [])
        
        if not data:
            error_msg = f"No manga found for search: {self.search_title}"
            logger.error(error_msg)
            sys.exit(error_msg)
        
        search_target = self.search_title.lower().strip()
        best_match = None
        
        for manga in data:
            manga_id = manga["id"]
            attributes = manga["attributes"]
            
            main_title_dict = attributes.get("title", {})
            main_title = next(iter(main_title_dict.values()), "Unknown Title")
            
            all_titles = [main_title]
            for alt_title_dict in attributes.get("altTitles", []):
                all_titles.extend(alt_title_dict.values())
                
            all_titles_clean = [t.lower().strip() for t in all_titles if t]
            logger.debug(f"Manga ID: {manga["id"]}, Manga Names: {all_titles_clean}")
            if search_target in all_titles_clean:
                
                display_title = main_title_dict.get('en')
                if not display_title:
                    for alt in attributes.get("altTitles", []):
                        if 'en' in alt:
                            display_title = alt['en']
                            break

                if not display_title:
                    display_title = next(iter(main_title_dict.values()), "Unknown Title")
                    
                best_match = (manga_id, display_title)
                logger.info(f"Exact match found. Selected Title: {display_title}")
                break
        
        if not best_match:
            first_manga = data[0]
            first_id = first_manga["id"]
            first_title_dict = first_manga["attributes"].get("title", {})
            first_title = next(iter(first_title_dict.values()), "Unknown Title")
            
            best_match = (first_id, first_title)
            logger.info(f"No exact match. Falling back to top API result: {first_title}")
        
        logger.info(f"Manga Id: {best_match[0]}, Title: {best_match[1]}")
        logger.info(f"End of getting the ID of the manga: {best_match[1]}")
        return best_match

    def __merge_subchapters(self,chapters_list):
        logger.info("Start of the merge of subchapters")
        
        subchapter_groups = defaultdict(list)
        for item in chapters_list:
            sub_key = (item.get('volume'), item.get('chapter'), item.get('sub_chapter'))
            subchapter_groups[sub_key].append(item)
        
        best_unique_chapters = []
        for sub_key, items in subchapter_groups.items():
            logger.debug(f"Grouped Data Subchapter: Volume: {sub_key[0]}, Chapter: {sub_key[1]}, Subchapter: {sub_key[2]}, items: {items}")
            if len(items) > 1:
                items.sort(key=lambda x: min(
                    scanlation_groups['preferred_groups'].index(y) if y in scanlation_groups['preferred_groups'] else 999 
                    for y in x['scanlation_group']
                ))
            best_unique_chapters.append(items[0])
        
        grouped_data = defaultdict(list)
        for item in best_unique_chapters:
            group_key = (item.get('volume'), item.get('chapter'))
            grouped_data[group_key].append(item)
        
        
        merged_results = []
        for (volume, chapter), items in grouped_data.items():
            items.sort(key=lambda x: x.get('sub_chapter') or 0)      
            logger.debug(f"Grouped Data Chapter: Volume: {volume}, Chapter: {chapter}, items: {items}")
            base_item = items[0].copy()
            
            if len(items) > 1:
                combined_img_data = []
                combined_groups = []
                for sub_item in items:
                    combined_img_data.extend(sub_item['img_data'])
                    for group in sub_item['scanlation_group']:
                        if group not in combined_groups:
                            combined_groups.append(group)

                base_item['img_data'] = combined_img_data
                base_item['scanlation_group'] = combined_groups
            
            all_sub_chapters = [
                sub.get('sub_chapter') for sub in items 
                if sub.get('sub_chapter') is not None
            ]
            
            base_item['sub_chapter'] = max(all_sub_chapters) if all_sub_chapters else 0 
            base_item['title'] = f"Vol. {volume} Ch. {chapter}"
            
            logger.debug(f"Merged Data: {base_item} - Groups: {base_item['scanlation_group']}")
            merged_results.append(base_item)
        logger.info("End of the merge of subchapters")
        return merged_results
    
    def __look_up_cover(self, manga_chapters):
        logger.info("Start of the look up for covers")
        
        params = {
            "manga[]": self.id, 
            "limit": 100,
            "locales[]": ["ja", "zh"]
        }
        
        logger.debug(f"Covers Request URL: {BASE_URL}/cover, Params: {params}")
        r_covers = self.session.get(f"{BASE_URL}/cover",params=params).json()['data']
        covers_data = []
        for cover in r_covers:
            covers_data.append({
                "id": cover["attributes"]['fileName'],
                "volume": cover["attributes"]['volume']
            })
        logger.debug(f"Covers: {covers_data}")
        
        cover_lookup = {}
        for cover in covers_data:
            vol = cover.get("volume")
            if vol is not None and '.' not in vol: 
                cover_lookup[int(vol)] = cover["id"]
        
        previous_cover_id = cover_lookup.get(1)
        if previous_cover_id is None and cover_lookup:
            previous_cover_id = list(cover_lookup.values())[0]
        
        for chapter in manga_chapters:
            chapter_vol = chapter.get("volume")
            if chapter_vol in cover_lookup:
                previous_cover_id = cover_lookup[chapter_vol]
                chapter["cover_id"] = ("https://uploads.mangadex.org", previous_cover_id)
                logger.debug(f"Chapter: {chapter}")
            else:
                chapter["cover_id"] = ("https://uploads.mangadex.org", previous_cover_id)
                logger.debug(f"Chapter: {chapter}")

        logger.info("End of the look up for covers")
        return manga_chapters

    def __instance_volume(self, manga_chapters):
        logger.info("Start of the setting None Volume Chapters to Max")
        max_volume = max((chapter['volume'] if chapter['volume'] is not None else 0) for chapter in manga_chapters) + 1
        for chapter in manga_chapters:
            if chapter['volume'] is None:
                logger.debug(f"Chapter to Change: {chapter}")
                chapter['volume'] = max_volume
                logger.debug(f"Changed chapter: {chapter}")
        logger.info("End of the setting None Volume Chapters to Max")
        return manga_chapters
    
    def get_chapters(self):
        logger.info(f"Start of getting the Chapters for the Manga: {self.title}")
        logger.debug(f"Chapter Request URL: {BASE_URL}/manga/{self.id}/feed, Params: 'translatedLanguage[]' : {LANGUAGES}")
        
        last_chapter, sub_chapter = self.db.get_last_chapter(self.url_id)
        r_chapters = self.session.get(
            f"{BASE_URL}/manga/{self.id}/feed",
            params={
                "translatedLanguage[]": LANGUAGES,
                "order[volume]": "asc",
                "order[chapter]": "asc",
                "limit": 200
            }
        )

        raw_chapters = []
        for chapter in r_chapters.json()['data']:
            scanlation_names = []
            user_names = []
            
            for relationship in chapter["relationships"]:
                if relationship['type'] == "scanlation_group":
                    logger.debug(f"Scanlation Group Request URL: {BASE_URL}/group/{relationship['id']}")
                    scanlation_names.append(self.session.get(f"{BASE_URL}/group/{relationship['id']}").json()["data"]["attributes"]["name"])
                elif relationship['type'] == "user":
                    logger.debug(f"User Request URL: {BASE_URL}/user/{relationship['id']}")
                    user_names.append(self.session.get(f"{BASE_URL}/user/{relationship['id']}").json()["data"]["attributes"]["username"])
            
            if not ((set(scanlation_names) & set(scanlation_groups['preferred_groups'])) or (set(user_names) & set(scanlation_groups['preferred_users']))):
                logger.info(f"Skip - Scanlation: {set(scanlation_names)}, User: {set(user_names)}")
                continue
            
            raw_chapters.append({
                "id": chapter['id'],
                "title" : chapter['attributes']['title'],
                "scanlation_group": scanlation_names,
                "user": user_names,
                "volume" : int(chapter['attributes']['volume']) if chapter['attributes']['volume'] is not None else None,
                "chapter" : int(chapter['attributes']['chapter'].split('.')[0]),
                "sub_chapter" : int(chapter['attributes']['chapter'].split('.')[1]) if len(chapter['attributes']['chapter'].split('.')) > 1 else 0
            })
            logger.debug(f"Manga Chapter: {raw_chapters[-1]}")
        
        raw_chapters = self.__instance_volume(raw_chapters)
        
        manga_chapters = []
        for chapter in raw_chapters:
            
            if last_chapter != 0:
                if chapter['chapter'] < last_chapter:
                    logger.info(f"Skip API: {chapter['id']} - Chapter {chapter['chapter']} already exists locally")
                    continue
                elif chapter['chapter'] == last_chapter:
                    if chapter['sub_chapter'] <= sub_chapter:
                        logger.info(f"Skip API: {chapter['id']} - Chapter {chapter['chapter']} (Sub {chapter['sub_chapter']}) already exists locally")
                        continue
                    else:
                        folder_path = self.main_folder / f"Volume_{chapter['volume']}" / f"Chapter_{chapter['chapter']}"
                        if folder_path.exists():
                            logger.debug(f"Deleting: {chapter['id']} - Chapter {chapter['chapter']} already exists locally")
                            shutil.rmtree(folder_path)
            
            time.sleep(1.1)
            
            logger.debug(f"Img Server Request URL: {BASE_URL}/at-home/server/{chapter['id']}")
            r_img = self.session.get(f"{BASE_URL}/at-home/server/{chapter['id']}").json()
            
            chapter["base_url"] = r_img["baseUrl"]
            chapter["img_data"] = [(r_img["chapter"]["hash"], img_path) for img_path in r_img["chapter"]["data"]]
            
            manga_chapters.append(chapter)
            logger.debug(f"Manga Chapter: {manga_chapters[-1]}")
        
        if not manga_chapters:
            logger.info( "This Manga is up to date! There is no need to download!")
            return
        
        manga_chapters = self.__look_up_cover(manga_chapters)
        
        logger.info(f"End of getting the Chapters for the Manga: {self.title}")
        return self.__merge_subchapters(sorted(manga_chapters, key=lambda chapter: (chapter['volume'], chapter['chapter'], (chapter['sub_chapter'] or 0))))

    def download(self):
        logger.info("Start of the download of each chapter")
        for chapter in self.chapters:
            logger.info(f"Downloading: {chapter['id']} - Chapter {chapter['chapter']} - {chapter['scanlation_group']}")
            
            folder_path = self.main_folder / f"Volume_{chapter['volume']}" / f"Chapter_{chapter['chapter']}"
            logger.debug(f"Path to save the Mangas: {folder_path}")
            
            folder_path.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Cover Img Request URL: {chapter['cover_id'][0]}/covers/{self.id}/{chapter['cover_id'][1]}")
            r_img_cover = self.session.get(f"{chapter['cover_id'][0]}/covers/{self.id}/{chapter['cover_id'][1]}")

            full_path = folder_path / f"SCT1-{chapter['cover_id'][1]}"
            with open(str(full_path), mode="wb") as f:
                f.write(r_img_cover.content)
            
            count = 2
            for page in chapter['img_data']:
                time.sleep(0.2)
                full_path = folder_path / f"SCT{count}-{chapter['cover_id'][1]}"
                
                logger.debug(f"Chapter Img Request URL: {chapter['base_url']}/data/{page[0]}/{page[1]}")
                logger.debug(f"Path to save the Img: {full_path}")
                r_chapter_img = self.session.get(f"{chapter['base_url']}/data/{page[0]}/{page[1]}")
                with open(str(full_path), mode="wb") as f:
                    f.write(r_chapter_img.content)
                count += 1

            logger.info(f"Downloaded {len(chapter['img_data'])} pages.")
        logger.info("End of the download of each chapter")
        
        latest_chapter_data = max(self.chapters, key=lambda x: x['chapter'])
        
        self.db.save_metadata(
            url_id = self.url_id,
            site_id = self.id,
            searched_name = self.search_title,
            saved_name = self.title,
            last_chapter = latest_chapter_data['chapter'],
            sub_chapter = latest_chapter_data['sub_chapter'],
            media_type = 'manga'
        )