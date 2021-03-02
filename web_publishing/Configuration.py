###############################################################################
# NAME:             Configuration.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      Contains logic useful for obtaining configuration.
#
# CREATED:          02/28/2021
#
# LAST EDITED:      02/28/2021
###

from importlib import resources
import logging

import yaml
from cerberus import Validator

def getConfiguration(configurationFileName):
    try:
        with open(configurationFileName) as configurationFile:
            document = yaml.load(''.join(configurationFile.readlines()),
                                 Loader=yaml.FullLoader)
        logging.info('Using configuration file.')
        documentSchema = yaml.load(resources.read_text(
            'web_publishing', 'schema.yaml'), Loader=yaml.FullLoader)
        validator = Validator(schema=documentSchema)
        validator.validate(document)
        return document
    except FileNotFoundError as e:
        logging.warning(str(e))
    return {}

def applyConfiguration(readConfig, defaultConfig):
    for key in defaultConfig:
        if key not in readConfig:
            if isinstance(defaultConfig[key], dict):
                applyConfiguration(readConfig[key], defaultConfig[key])
            readConfig[key] = defaultConfig[key]
    return readConfig

CONFIG_DEFAULTS = {
    'DocumentRoot': './',
    'BuildDirectory': '.pdflatex',
    'ServerPDFPath': 'pdf',
    'ServerKeepPDFPath': False,
    'PageData': [],
    'minted': True,
    'BuildExclude': [],
    'MiddlemanDirectory': 'source',
    'Host': '',
    'RemotePath': '',
    'Books': {},
    'BookExclude': [],
    'WebIndex': '',
    'BookRoot': './',
    'CopyFiles': [],
}

###############################################################################
