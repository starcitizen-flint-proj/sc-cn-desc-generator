import sys
import yaml
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import config
from module.paratranz_filler import ParatranzFiller

if __name__ == '__main__':
    
    logging.basicConfig(level=logging.WARNING, force=True)

    with open('config.yaml', 'r', -1, config.ENCODE) as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
        proj_id     = config_data['paratranz']['proj_id']
        auth_token  = config_data['paratranz']['token']

    filler = ParatranzFiller(proj_id=proj_id, auth_token=auth_token, verbose=True)
    filler.run()
