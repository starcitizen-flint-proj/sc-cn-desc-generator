import logging

logging.basicConfig(level=logging.WARN, force=True)

TEXT_FILE_DIR    = 'data'

EN_FILE_NAME     = 'en.ini'     # 英文原文
CN_FILE_NAME     = 'cn.ini'     # 全汉化
REF_FILE_NAME    = 'ref.ini'    # 参考（双语汉化）
RSUI_FILE_NAME   = 'rsui.ini'   # 社区增强

EN_DOWNLOAD_URL  = "https://ini.42kit.com/orginal/global.ini"
CN_DOWNLOAD_URL  = "https://ini.42kit.com/full/global.ini"
REF_DOWNLOAD_URL = "https://ini.42kit.com/both/global.ini"
# TODO RSUI增强汉化下载链接

ENCODE = 'utf-8-sig'
UNKNOWN_CHR = '\ufffd'
REPLACE_CHR = ' '