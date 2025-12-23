import logging
import yaml

import src.config as config
from module.paratranz_filler import ParatranzFiller

if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO, force=True)

    with open('config.yaml', 'r', -1, config.ENCODE) as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
        proj_id     = config_data['paratranz']['proj_id']
        auth_token  = config_data['paratranz']['token']

    filler = ParatranzFiller(proj_id=proj_id, auth_token=auth_token)
    filler.run()