###############################################################################
# NAME:             Files.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      Contains classes for handling different file types.
#
# CREATED:          02/24/2021
#
# LAST EDITED:      02/28/2021
###

import logging
import os
import re

class WebFile:
    def __init__(self, filePath):
        self.filePath = os.path.relpath(filePath)
        if not os.path.isfile(filePath):
            raise FileNotFoundError(filePath)

    def getPath(self):
        return self.filePath

    @classmethod
    def getComponentsOfPath(cls, filePath):
        components = []
        if filePath == '.':
            return components
        while True:
            if not filePath:
                return components
            filePath, tail = os.path.split(filePath)
            if tail:
                components.insert(0, tail)

###############################################################################
# LaTeX Files
#
# Things we do with LaTeX files.
###

def getPdflatexFlags(minted):
    defaultHandler = lambda argument: argument
    pdflatexFlags = {
        # Should not disable this one--allows us to script pdflatex
        '-interaction=batchmode': {'set': True, 'handler': defaultHandler},

        # Only needed for minted
        '-shell-escape': {'set': minted, 'handler': defaultHandler},
    }

    # I've tried.
    return ' '.join(list(map(
        # pylint: disable=unnecessary-lambda
        lambda key: pdflatexFlags[key]['handler'](key),
        [key for key in pdflatexFlags if pdflatexFlags[key]['set']]
    )))

PDF_RULE_FORMAT = """
{}: {}
	mkdir -p {}
	export pdfFile=$(shell realpath $<) && cd {} && \\
		pdflatex $(pdflatexFlags) $$pdfFile $(redirect)
	export pdfFile=$(shell realpath $<) && cd {} && \\
		pdflatex $(pdflatexFlags) $$pdfFile $(redirect)
	mkdir -p $(@D)
	-mv {}$(basename $(<F)).pdf $@
"""
def generatePdfRule(target, prerequisite, buildDirectory,
                    *additionalPrerequisites):
    prerequisites = prerequisite
    if additionalPrerequisites:
        prerequisites = ' '.join([prerequisite]
                                 + list(additionalPrerequisites))
    return PDF_RULE_FORMAT.format(
        target, prerequisites, buildDirectory, buildDirectory, buildDirectory,
        buildDirectory + os.sep)

HTML_RULE_FORMAT = """
{}: {}
	export htmlFile=$(shell realpath $<) {} && cd {} && \\
		make4ht -sm draft {}-f html5+tidy+join_colors $$htmlFile \\
		$(redirect)
	-mkdir -p $(@D)
	-mv {}$(basename $(<F)).html $@
	-mv {}$(basename $(<F)).css $(basename $@).css
"""
def generateHtmlRule(target, prerequisite, buildDirectory, tex4htConfig,
                     *additionalPrerequisites):
    prerequisites = prerequisite
    if additionalPrerequisites:
        prerequisites = ' '.join([prerequisite]
                                 + list(additionalPrerequisites))
    setTeX4htConfig = '&& export tex4htCfg=$(shell realpath tex4ht.cfg)'
    return HTML_RULE_FORMAT.format(
        target,
        prerequisites,
        setTeX4htConfig if tex4htConfig else '',
        buildDirectory,
        '-c tex4ht.cfg ' if tex4htConfig else '',
        buildDirectory + os.sep, buildDirectory + os.sep)

ERB_RULE_FORMAT = """
{}: {}
	mkdir -p $(@D)
	wp-prepare -d '{}' $< $(basename $<).css $@
"""
def generateErbRule(target, prerequisite, pageData):
    return ERB_RULE_FORMAT.format(
        target, prerequisite,
        ','.join([f'{key}={pageData[key]}' for key in pageData]))

class LaTeXFile(WebFile):
    def __init__(self, path, rootDirectory='doc', buildDirectory='.pdflatex',
                 serverPdfPath='pdf', serverKeepPdfPath=False,
                 pageData=None, minted=True, middlemanDirectory='source',
                 bookFile=False, webIndex=False, sourcesDirPrefix='sources-'):
        super().__init__(path)
        self.withoutExt = ''
        self.files = {
            'pdf': '',
            'erb': '',
            'html': '',
            'additional-prerequisites': [],
        }
        self.conf = {
            'rootdir': os.path.relpath(rootDirectory),
            'build': buildDirectory,
            'erbpath': middlemanDirectory,
            'server': {
                'pdfpath': serverPdfPath, 'keeppdfpath': serverKeepPdfPath
            },
            'pagedata': {} if not pageData else pageData,
            'tex4htconfig': os.path.isfile('tex4ht.cfg'),
            'minted': minted,
            'isbook': bookFile,
            'webindex': webIndex,
            'sourcesdirprefix': sourcesDirPrefix,
        }
        if self.conf['pagedata']:
            logging.info('%s: Using pageData=%s', self.getPath(),
                         str(self.conf['pagedata']))
        self.setPathComponents()

    def setPathComponents(self):
        rootDirectory = self.conf['rootdir']
        if not os.path.isdir(rootDirectory):
            raise FileNotFoundError(rootDirectory)
        partsNoExtension = WebFile.getComponentsOfPath(
            os.path.splitext(self.getPath())[0])
        directorySlice = len(WebFile.getComponentsOfPath(rootDirectory))
        noExtensionNoRoot = partsNoExtension[directorySlice:]
        if self.conf['webindex']:
            noExtensionNoRoot[-1] = 'index'
        self.withoutExt = os.path.join(*noExtensionNoRoot)

        # Now that we have the raw paths without extensions, set the target
        # paths
        if not self.conf['isbook']:
            self.setPagePaths()
        self.setBookPaths()

    def setBookPaths(self):
        if self.conf['server']['keeppdfpath']:
            self.files['pdf'] = os.path.join(self.conf['server']['pdfpath'],
                                        self.withoutExt + '.pdf')
        else:
            self.files['pdf'] = os.path.join(
                self.conf['server']['pdfpath'],
                os.path.split(self.withoutExt)[1] + '.pdf')

    def setPagePaths(self):
        self.files['html'] = os.path.join(self.conf['build'],
                                     self.withoutExt + '.html')
        self.files['erb'] = os.path.join(self.conf['erbpath'],
                                    self.withoutExt + '.html' + '.erb')

    def addCopyRulesForSources(self, makefile):
        parentDir, basenameNoExt = os.path.split(self.withoutExt)
        sourcesDirPrerequisite = os.path.join(
            parentDir, self.conf['sourcesdirprefix'] + basenameNoExt)
        if not os.path.isdir(sourcesDirPrerequisite):
            return

        # Add sourcesDirPrerequisite to additional prerequisites
        logging.info('Copying sources dir %s', sourcesDirPrerequisite)
        for dirpath, _, filenames in os.walk(sourcesDirPrerequisite):
            for filename in filenames:
                target = os.path.join(
                    self.conf['build'],
                    self.conf['sourcesdirprefix'] + basenameNoExt,
                    filename)
                self.files['additional-prerequisites'].append(target)
                makefile.addCopyRule(target,
                    os.path.join(dirpath, filename))

    def addPageRules(self, makefile):
        # Add ERB Rule
        # TODO: Add .css file as a prerequisite for ERB file
        if '$(erbFiles)' not in makefile.getDefaultRulePrerequisites():
            makefile.getDefaultRulePrerequisites().append('$(erbFiles)')
        makefile.appendToVariable('erbFiles', self.files['erb'])
        makefile.addRule(generateErbRule(self.files['erb'], self.files['html'],
                                         self.conf['pagedata']))

        # Add tex4ht.cfg copy rule
        htmlPrerequisites = []
        if self.conf['tex4htconfig']:
            tex4htConfigFile = 'tex4ht.cfg'
            tex4htConfigTarget = os.path.join(
                self.conf['build'], tex4htConfigFile)
            makefile.addCopyRule(tex4htConfigTarget, tex4htConfigFile)
            htmlPrerequisites.append(tex4htConfigTarget)

        # Grab the sources dir for this file
        self.addCopyRulesForSources(makefile)

        # Add HTML rules
        makefile.appendToVariable('htmlFiles', self.files['html'])
        makefile.addRule(generateHtmlRule(
            self.files['html'], self.getPath(), self.conf['build'],
            self.conf['tex4htconfig'], *htmlPrerequisites,
            *self.files['additional-prerequisites']))

    @classmethod
    def tryGetDependencyFrom(cls, line, command, argumentNumber,
                             fileExtension):
        if command in line:
            components = re.findall(r"[^{}\[\]]+", line)
            if argumentNumber >= len(components):
                return []
            potentialDependency = components[argumentNumber] + fileExtension
            if os.path.isfile(potentialDependency):
                logging.info('Discovered dependency %s', potentialDependency)
                return [potentialDependency]
            return []
        return []

    def getProjectDependencies(self):
        with open(self.getPath(), 'r') as latexFile:
            deps = []
            for line in latexFile.readlines():
                deps.extend(self.tryGetDependencyFrom(
                    line, '\\documentclass', 1, '.cls'))
                deps.extend(self.tryGetDependencyFrom(
                    line, '\\documentclass', 2, '.cls'))
                deps.extend(self.tryGetDependencyFrom(
                    line, '\\documentclass', 1, ''))
                deps.extend(self.tryGetDependencyFrom(
                    line, '\\subfile', 1, '.tex'))
            return deps

    def addRules(self, makefile):
        # Add Project Dependencies
        for filename in self.getProjectDependencies():
            target = os.path.join(self.conf['build'], filename)
            self.files['additional-prerequisites'].append(target)
            makefile.addCopyRule(target, filename)

        if not self.conf['isbook']:
            self.addPageRules(makefile)

        if '$(pdfFiles)' not in makefile.getDefaultRulePrerequisites():
            makefile.getDefaultRulePrerequisites().append('$(pdfFiles)')
        makefile.appendToVariable('pdfFiles', self.files['pdf'])
        if not makefile.variableIsSet('pdflatexFlags'):
            makefile.appendToVariable(
                'pdflatexFlags', getPdflatexFlags(
                    minted=self.conf['minted'],
                ))
        makefile.addRule(generatePdfRule(
            self.files['pdf'], self.getPath(), self.conf['build'],
            *self.files['additional-prerequisites']))

###############################################################################
