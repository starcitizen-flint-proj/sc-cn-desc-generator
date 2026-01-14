import os
import re
import json
import logging
from typing import List, Tuple

import src.config as config

class DescTemplateReplacer():
    
    def __merge_path(self, file_path, base_path = config.TEXT_FILE_DIR):
        return os.path.join(base_path, file_path)
    
    def __init__(
        self,
        map_files: dict | None = None
    ):
        self.keys = set()
        self.json_data = dict()
        # NOTE 更新模板替换文件后需要对应的在这里进行修改
        map_files = {
            'keys':             self.__merge_path('keys.json'),
            'effects':          self.__merge_path('effects.json'),
            'manufacturers':    self.__merge_path('manufacturers.json'),
            'general_values':   self.__merge_path('general_values.json'),
        } if map_files is None else map_files
        direct_load = {
            'keys':             map_files['keys'],
            'effects':          map_files['effects'],
            'manufacturers':    map_files['manufacturers'],
        }
        
        for key, path in direct_load.items():
            with open(path, 'r', encoding=config.ENCODE) as file:
                self.json_data[key] = json.load(file)['data']
        with open(map_files['keys'], 'r', encoding=config.ENCODE) as file:
            self.keys.update(json.load(file)['data'].keys())
        with open(map_files['general_values'], 'r', encoding=config.ENCODE) as file:
            self.general_values = json.load(file)
    
    def __pre_proc(self, s: str):
        s = s.replace('/u00a0', ' ')
        s = s.replace('/xa0', ' ')
        s = re.sub('^ {1,}', '', s)
        s = re.sub(' {1,}$', '', s)
        return s
    
    def __match_number(self, s):
        pattern = re.compile(r'[+-]?\d+\.?\d*|N/A')
        if pattern.match(s):
            return re.sub(pattern, '<<NUM>>', s)
        return None
    
    def __map_number(self, s, template: tuple[str, str]):
        pattern, replace_template = template
        pattern = re.escape(pattern)
        pattern = pattern.replace('<<NUM>>', r'([+-]?\d+\.?\d*|N/A)')
        compiled_pattern = re.compile(f'^{pattern}$')
        match_result = compiled_pattern.match(s)
        
        if match_result:
            groups = match_result.groups()
            result = replace_template
            for group in groups:
                result = result.replace('<<NUM>>', group, 1)
            return result

        return None
    
    def __replace_line(self, line: str):
        key, _, value = line.partition(': ')
        key, value = self.__pre_proc(key), self.__pre_proc(value)
        # 检查是不是在替换列表里
        if key not in self.keys:
            return line, False
        
        matched_key = self.json_data['keys'].get(key, key)
        # NOTE 特殊检查项
        # 特殊检查：制造商
        if key == 'Manufacturer':
            return f"{matched_key}：{self.json_data['manufacturers'].get(value, value)}（{value}）", True
        # 特殊检查：食物/饮品的效果
        if key == 'Effect' or key == 'Effects':
            effects = [self.__pre_proc(e) for e in value.split(',')]
            return f"{matched_key}：{'，'.join([self.json_data['effects'].get(e, e) for e in effects])}", True
        # 其他检查
        if value in self.general_values[key].keys():
            return f"{matched_key}：{self.general_values[key][value]}", True
        # 数值检查
        num_match = self.__match_number(value)
        if num_match is not None:
            replaced_num = self.__map_number(value, (num_match, self.general_values[key][num_match]))
            if replaced_num is not None:
                return f"{matched_key}：{replaced_num}", True
            else:
                logging.warning(f"数值模板替换失败：{value} | {num_match}, {self.general_values[key][num_match]} | {replaced_num}")
            
        # key在范围里但是没啥特殊处理的通配符
        if value is None or value == 'None':
            logging.warning(f"{line} | {matched_key}：[未翻译]{value}")
        return f"{matched_key}：[未翻译]{value}", True
    
    def replace(self, original_str: str, return_original: bool = False):
        replaced_list = []
        flag = False
        for line in original_str.split('\\n'):
            if line.count(': ') != 1: 
                # 跳过不打算替换的
                replaced_list.append(line)
                continue
            result, is_replaced = self.__replace_line(line)
            flag = flag or is_replaced
            replaced_list.append(result)
        notice_str = '【\\n编辑后请删除中括号以及中括号以内的内容\\n注意：此为自动填充的模板翻译，文本没有完全翻译且已填充部分可能存在错误，请仔细核对！\\n】'
        
        if flag: return notice_str + '\\n'.join(replaced_list)
        
        return original_str if return_original else ''
    