import os, re
import logging
import requests
import module.config as config
from tqdm import tqdm
from io import TextIOWrapper
from abc import ABC, abstractmethod

def read_file_lines(file: TextIOWrapper) -> list[str]:
    content = file.read().replace(config.UNKNOWN_CHR, config.REPLACE_CHR)
    lines = content.splitlines()
    return lines

class BaseTextProcessor(ABC):
    
    def __init__(self): pass
    
    @abstractmethod
    def process(self, text) -> str: pass
    
class GeneralProcessor(BaseTextProcessor):
    
    def __init__(self):
        super().__init__()
    
    def process(self, text: str):
        text = re.sub('： *', '：', text)
        text = text.replace('\xa0', ' ')
        return text

class TextReader():
    
    def __init__(
        self,
        base_path: str = config.TEXT_FILE_DIR,
        en_file: str = config.EN_FILE_NAME,
        cn_file: str = config.CN_FILE_NAME,
        pre_processor: BaseTextProcessor | None = None
    ) -> None:
        self.id_set  = set()
        self.en_dict = dict()
        self.cn_dict = dict()
        with open(os.path.join(base_path, en_file), 'r', encoding=config.ENCODE, errors='replace') as file:
            logging.info(f"Reading {os.path.join(base_path, en_file)}")
            for line in read_file_lines(file):
                tid, _, text = line.partition('=')
                self.id_set.add(tid)
                self.en_dict[tid] = text if pre_processor is None else pre_processor.process(text)
        with open(os.path.join(base_path, cn_file), 'r', encoding=config.ENCODE, errors='replace') as file:
            logging.info(f"Reading {os.path.join(base_path, cn_file)}")
            for line in read_file_lines(file):
                tid, _, text = line.partition('=')
                self.id_set.add(tid)
                self.cn_dict[tid] = text if pre_processor is None else pre_processor.process(text)
    
    def get(self, tid: str | list):
        if isinstance(tid, str):
            if tid not in self.id_set: return None
            return {
                'en': self.en_dict.get(tid),
                'cn': self.cn_dict.get(tid)
            }
        ret_data = dict()
        for id in tid:
            ret_data[id] = {
                'en': self.en_dict.get(id),
                'cn': self.cn_dict.get(id)
            }
        return ret_data
    
    def find_ids_by_pattern(self, pattern: str | re.Pattern[str], ignore_case: bool = False):
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        if ignore_case:
            return set([tid for tid in self.id_set if pattern.match(tid.lower())])
        return set([tid for tid in self.id_set if pattern.match(tid)])

def download_files():
    download_config = [
        (config.EN_DOWNLOAD_URL,  config.EN_FILE_NAME),
        (config.CN_DOWNLOAD_URL,  config.CN_FILE_NAME),
        (config.REF_DOWNLOAD_URL, config.REF_FILE_NAME),
    ]
    for url, file_name in download_config:
        file_path = os.path.join(config.TEXT_FILE_DIR, file_name)
        logging.info(f"Downloading {file_path} from {url}...")
        response = requests.get(url, stream=True)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
        logging.info(f"Download {file_name} complete.")