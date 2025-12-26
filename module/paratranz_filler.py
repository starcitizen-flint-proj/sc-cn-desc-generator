import re
import json
import logging
import requests

from module.replacer import DescTemplateReplacer

class ParatranzFiller():
    
    def __init__(self, proj_id: int | str, auth_token: str, page_size: int = 100, base_url: str = 'https://paratranz.cn/api', verbose=False) -> None:
        self.proj_id    = proj_id
        self.auth_token = auth_token
        self.page_size  = page_size
        self.base_url   = base_url
        self.verbose    = verbose
        
        self.replacer   = DescTemplateReplacer()
        self.target_ids = set()
        self.data = dict()
    
    def __proc_page(self, results):
        for r in results:
            if re.match(r'^item_desc.*', str(r['key']).lower()) is None:
                continue
            self.target_ids.add(r['id'])
            self.data[r['id']] = r
    
    def get_todo_desc(self, api_path: str = '/projects/{projectId}/strings'):
        url = self.base_url + api_path.format(projectId = self.proj_id)
        headers = {'Authorization': self.auth_token}
        params = {
            'stage': 0, # 指定未翻译的
            'page': 1,
            'pageSize': self.page_size,
        }
        response = requests.request("GET", url, headers=headers, params=params)
        response.raise_for_status()
        total_page = response.json()['pageCount']
        logging.info(f"共约{self.page_size * total_page}条未翻译条目，开始筛选描述条目")
        
        self.target_ids = set()
        self.data = dict()
        for page in range(total_page):
            params['page'] = page+1
            response = requests.request("GET", url, headers=headers, params=params)
            response.raise_for_status()
            self.__proc_page(response.json()['results'])
        
        logging.info(f"共{len(self.target_ids)}条未翻译的描述")
        return self.target_ids
    
    def run(self, api_path: str = '/projects/{projectId}/strings/{stringId}'):
        get_headers = {
            'Authorization': self.auth_token
        }
        put_headers = {
            'Content-Type': 'application/json',
            'Authorization': self.auth_token
        }
        
        if len(self.target_ids) == 0:
            self.get_todo_desc()
        
        count = 0
        for id in self.target_ids:
            logging.info(f"开始处理 id: {id}, key: {self.data[id]['key']}")
            url = self.base_url + api_path.format(projectId=self.proj_id, stringId=id)
            response = requests.request("GET", url, headers=get_headers)
            response.raise_for_status()
            
            if int(response.json()['stage']) != 0:
                logging.info(f"ID{id} 已经更新，跳过")
                continue
            translation = self.replacer.replace(response.json()['original'])
            if translation == '':
                logging.info(f"ID{id} 无匹配，跳过")
                continue
            
            payload = json.dumps({
                "stage": 0,
                "translation": translation
            })
            logging.debug(payload)
            response = requests.request("PUT", url, headers=put_headers, data=payload)
            response.raise_for_status()
            logging.info(f"ID{id} 匹配成功，已填充: {response.json()['translation']}")
            count += 1
        
        return count
