###############################################################################
# NAME:             Locator.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      Tools useful for locating files.
#
# CREATED:          02/25/2021
#
# LAST EDITED:      02/26/2021
###

from os import walk, path
import logging

class Locator:
    def __init__(self, buildExclude=None):
        self.buildExclude = buildExclude
        if not buildExclude:
            self.buildExclude = []

    def isExcluded(self, filename):
        if self.buildExclude and filename in self.buildExclude:
            logging.info('Excluding %s', filename)
            return True
        return False

    def locate(self, rootDirectory, extension):
        # Locate all files with extension in rootDirectory
        latexFiles = []
        logging.info('Recursively searching %s for %s files...',
                     rootDirectory, extension)
        for dirpath, _, filenames in walk(rootDirectory):
            for filename in filenames:
                relativePath = path.relpath(path.join(dirpath, filename))
                _, thisExtension = path.splitext(relativePath)
                if thisExtension == extension \
                   and not self.isExcluded(relativePath):
                    logging.info('Adding %s', relativePath)
                    latexFiles.append(relativePath)
        return latexFiles


###############################################################################
