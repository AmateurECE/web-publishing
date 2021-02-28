###############################################################################
# NAME:             GenerateMakefile.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      Creates a makefile for the project.
#
# CREATED:          07/18/2020
#
# LAST EDITED:      02/28/2021
###

import argparse
from importlib import resources
import logging
import os

import yaml
from cerberus import Validator

from .Files import LaTeXFile
from .Makefile import Makefile
from .Locator import Locator

# TODO: Allow attachment of raw script files
# TODO: Copyright notice and table of contents for the book?
# TODO: Validate books
BUILD_RULE_RECIPE = """
	wp-navigation{} -d '{}' $(htmlFiles)
	middleman build
"""
def getBuildRuleRecipe(book=False, buildDirectory='.'):
    return BUILD_RULE_RECIPE.format(' -b' if book else '', buildDirectory)

DEPLOY_RULE = """
host={}
remotePath={}
deploy: build
	rsync -r -e 'ssh -p 5000' --delete build/ pdf \\
		"$(host):$(remotePath)"
"""
def getDeployRule(host='edtwardy@edtwardy.hopto.org',
                  remotePath='/var/www/edtwardy.hopto.org/repository/'):
    return DEPLOY_RULE.format(host, remotePath)

SET_REDIRECT = """
ifneq ($(V),1)
redirect = 2>&1 >/dev/null
endif
"""

def verifyBookMain(bookMain, latexFiles):
    """Verifies that the bookMain file contains all other latexFiles."""
    with open(bookMain, 'r') as bookMainFile:
        bookText = ''.join(bookMainFile.readlines())
        for latexFile in latexFiles:
            if f'\\subfile{{{latexFile.replace(".tex", "")}}}' not in bookText:
                logging.warning(('%s is not included in %s and not excluded'
                                 ' in makefile_config.py'),
                                latexFile, bookMain)

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

def setUpMakefile(config, copyFiles):
    makefile = Makefile()
    makefile.setDefaultRuleTarget('build')
    makefile.setDefaultRuleRecipe(getBuildRuleRecipe(
        # TODO: Enable book link generation
        # book=bool(config['Books']),
        buildDirectory=config['BuildDirectory']))
    makefile.addRule(getDeployRule(
        host=config['Host'], remotePath=config['RemotePath']))
    makefile.addRule(SET_REDIRECT)
    for filename in copyFiles:
        makefile.addCopyRule(
            os.path.join(config['BuildDirectory'], filename), filename)
    return makefile

def generateMakefile(makefile, bookFiles=None, latexFiles=None, config=None):
    bookFiles = [] if not bookFiles else bookFiles
    latexFiles = [] if not latexFiles else latexFiles
    config = {} if not config else config
    for latexFile in latexFiles:
        pageData = {}
        if latexFile in config['PageData']:
            pageData = config['PageData'][latexFile]
        latexFileInstance = LaTeXFile(
            latexFile, rootDirectory=config['DocumentRoot'],
            buildDirectory=config['BuildDirectory'],
            serverPdfPath=config['ServerPDFPath'],
            serverKeepPdfPath=config['ServerKeepPDFPath'],
            pageData=pageData,
            minted=config['minted'],
            middlemanDirectory=config['MiddlemanDirectory'],
            bookFile=bool(latexFile in bookFiles),
            webIndex=latexFile == config['WebIndex'],
        )
        latexFileInstance.addRules(makefile)
    with open('Makefile', 'w') as outputFile:
        makefile.write(outputFile)

def getArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--config-file', help=('The configuration file'),
                        default='./web-publishing.yaml')
    parser.add_argument('-v', help='Enable verbose log output',
                        action='store_true', default=False)
    parser.add_argument(
        '-c', '--copy-files', help=(
            'A comma-separated list. For each file in the list, generate a'
            ' rule in the makefile that copies this file to the build'
            ' directory at build time. Useful for ensuring successful'
            ' compilation of files that rely on .cls or .tex files that reside'
            ' in the cwd.'), default='')
    return parser.parse_args()

def main():
    # Obtain the command line arguments
    args = getArguments()
    if args.v:
        logging.basicConfig(level=logging.DEBUG)

    # Obtain the configuration
    config = applyConfiguration(
        getConfiguration(args.config_file), CONFIG_DEFAULTS)
    logging.info(config)

    # Set up the Makefile
    if args.copy_files:
        config['CopyFiles'].extend(args.copy_files.split(','))
    makefile = setUpMakefile(config, config['CopyFiles'])

    # Obtain all latex files (excluding those in the build directory)
    locator = Locator()
    buildExclude = locator.locate(config['BuildDirectory'], '.tex')
    locator = Locator(buildExclude=buildExclude + config['BuildExclude'])
    generateMakefile(
        makefile,
        bookFiles=list(config['Books'].keys()),
        latexFiles=locator.locate(config['DocumentRoot'], '.tex'),
        config=config
    )

if __name__ == '__main__':
    main()

###############################################################################
