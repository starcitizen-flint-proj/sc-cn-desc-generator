import sys
import json
import yaml
import logging
import requests
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import config
from module.paratranz_filler import ParatranzFiller

def ntfy_msg_send(title, message, topic):
    requests.post("https://ntfy.sh.zapping.top/",
    data=json.dumps({
            "topic": topic,
            "message": str(message),
            "title": str(title),
            # "delay": delay
            # "tags": ["warning","cd"],
            # "priority": 4,
            # "attach": "https://filesrv.lan/space.jpg",
            # "filename": "diskspace.jpg",
            # "click": "https://homecamera.lan/xasds1h2xsSsa/",
            # "actions": [{ "action": "view", "label": "Admin panel", "url": "https://filesrv.lan/admin" }]
        })
    )

def main():
    logging.basicConfig(level=logging.WARNING, force=True)

    with open('config.yaml', 'r', -1, config.ENCODE) as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
        proj_id     = config_data['paratranz']['proj_id']
        auth_token  = config_data['paratranz']['token']

    filler = ParatranzFiller(proj_id=proj_id, auth_token=auth_token, verbose=True)
    print("开始拉取数据")
    num = filler.check()
    print(f"共{num}条可被填充文本")
    if num != 0:
        ntfy_msg_send("Paratranz数据更新", f"更新了{num}条可被填充文本", 'general')

if __name__ == '__main__':
    main()