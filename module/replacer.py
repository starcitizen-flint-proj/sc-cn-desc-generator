import os, re
from typing import List, Tuple

import src.config as config

class NumTemplateReplacer:
    def __init__(self, template_file: str):
        """
        初始化模板替换器
        
        Args:
            template_file: 模板文件路径
        """
        self.templates = self._load_templates(template_file)
    
    def _load_templates(self, template_file: str) -> List[Tuple[re.Pattern, str]]:
        """
        加载模板文件并转换为正则表达式
        
        Args:
            template_file: 模板文件路径
            
        Returns:
            包含(正则表达式模式, 替换模板)的列表
        """
        templates = []
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):  # 跳过空行和注释
                        continue
                    
                    # 分割模式和替换文本
                    if '=' in line:
                        pattern_str, replacement = line.split('=', 1)
                        
                        # 手动构建正则表达式
                        # 先替换[NUM]为临时占位符
                        regex_pattern = pattern_str.replace('[NUM]', '<<<NUM>>>')
                        
                        # 转义其他正则特殊字符
                        regex_pattern = re.escape(regex_pattern)
                        
                        # 将占位符替换为正则表达式组
                        regex_pattern = regex_pattern.replace('<<<NUM>>>', r'(\d+(?:\.\d+)?|NA|N/A)')
                        
                        # 编译正则表达式（完全匹配）
                        try:
                            compiled_pattern = re.compile(f'^{regex_pattern}$')
                            templates.append((compiled_pattern, replacement))
                        except re.error as e:
                            print(f"警告: 第 {line_num} 行模板编译失败: {e}")
                    else:
                        print(f"警告: 第 {line_num} 行格式错误，缺少'='")
        
        except FileNotFoundError:
            print(f"警告: 模板文件 '{template_file}' 未找到")
        except Exception as e:
            print(f"错误: 加载模板文件时出错: {e}")
        
        return templates
    
    def replace(self, text: str) -> str:
        """
        使用模板替换文本
        
        Args:
            text: 输入文本
            
        Returns:
            替换后的文本，如果没有匹配则返回原文
        """
        for pattern, replacement_template in self.templates:
            match = pattern.match(text)
            if match:
                # 提取匹配的数字/NA/N/A
                groups = match.groups()
                
                # 替换模板中的[NUM]
                result = replacement_template
                for group in groups:
                    result = result.replace('[NUM]', group, 1)
                
                return result
        
        # 没有匹配，返回原文
        return text
    
    def replace_batch(self, texts: List[str]) -> List[str]:
        """
        批量替换文本
        
        Args:
            texts: 输入文本列表
            
        Returns:
            替换后的文本列表
        """
        return [self.replace(text) for text in texts]
    
    def get_template_count(self) -> int:
        """
        获取加载的模板数量
        
        Returns:
            模板数量
        """
        return len(self.templates)

class DescTemplateReplacer():
    
    def __merge_path(self, file_path, base_path = config.TEXT_FILE_DIR):
        return os.path.join(base_path, file_path)
    
    def __init__(
        self,
        map_files: dict | None = None
    ):
        # NOTE 更新模板替换文件后需要对应的在这里进行修改
        self.num_replacer = NumTemplateReplacer(self.__merge_path('num_templates.map'))
        if map_files is None:
            map_files = {
                'keys': self.__merge_path('keys.map'),
                'effects': self.__merge_path('effects.map'),
                'manufacturers': self.__merge_path('manufacturers.map'),
                'num_templates': self.__merge_path('num_templates.map')
            }
        self.map_files = {
            'keys':          map_files['keys'],
            'effects':       map_files['effects'],
            'manufacturers': map_files['manufacturers'],
            'num_templates': map_files['num_templates'],
            # TODO 其他对应关系暂时先没写，先看看效果
        }
        
        self.map_data = dict()
        for key, path in self.map_files.items():
            self.map_data[key] = dict()
            with open(path, 'r', -1, config.ENCODE) as file:
                for line in file.readlines():
                    text, _, replace = line.removesuffix('\n').partition('=')
                    self.map_data[key][text] = replace
            
        self.keys = set()
        with open(self.map_files['keys'], 'r', -1, config.ENCODE) as file:
            self.keys.update([line.partition('=')[0] for line in file.readlines()])
    
    def __proc(self, s: str):
        s = s.replace('/u00a0', ' ')
        s = s.replace('/xa0', ' ')
        s = re.sub('^ {1,}', '', s)
        s = re.sub(' {1,}$', '', s)
        return s
    
    def __replace_line(self, line: str):
        key, _, value = line.partition(': ')
        key, value = self.__proc(key), self.__proc(value)
        # 检查是不是在替换列表里
        if key not in self.keys:
            return line, False
        
        # 特殊检查：制造商
        if key == 'Manufacturer':
            return f"制造商：{self.map_data['manufacturers'].get(value, value)} ({value})", True
        # 特殊检查：食物/饮品的效果
        if key == 'Effect' or key == 'Effects':
            effects = [self.__proc(e) for e in value.split(',')]
            return f"效果：{'，'.join([self.map_data['effects'].get(e, e) for e in effects])}", True
        # TODO 其他检查
        
        # key在范围里但是没啥特殊处理的通配符（目前value保留原文）
        # 顺便处理 特殊检查：数值类
        return f"{self.map_data['keys'].get(key, key)}：{self.num_replacer.replace(value)}", True
    
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
    