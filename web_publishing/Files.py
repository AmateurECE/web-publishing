###############################################################################
# NAME:             Files.py
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      Contains classes for handling different file types.
#
# CREATED:          02/24/2021
#
# LAST EDITED:      02/27/2021
###

import os
import logging

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

    def addPageRules(self, makefile):
        # Add ERB Rule
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
        parentDir, basenameNoExt = os.path.split(self.withoutExt)
        sourcesDirTarget = os.path.join(
            self.conf['build'], self.conf['sourcesdirprefix'] + basenameNoExt)
        sourcesDirPrerequisite = os.path.join(
            parentDir, self.conf['sourcesdirprefix'] + basenameNoExt)
        if os.path.isdir(sourcesDirPrerequisite):
            logging.info('Copying sources dir %s', sourcesDirPrerequisite)
            makefile.addCopyRule(sourcesDirTarget, sourcesDirPrerequisite)
        # TODO: Add sourcesDirPrerequisite to additional prerequisites
        # TODO: Detect whether this file depends on other LaTeX files in the
        #       project (e.g. base .tex files (subfiles), .cls or .sty files)
        #       and add them to additional prerequisites

        # Add HTML rules
        makefile.appendToVariable('htmlFiles', self.files['html'])
        makefile.addRule(generateHtmlRule(
            self.files['html'], self.getPath(), self.conf['build'],
            self.conf['tex4htconfig'], *htmlPrerequisites))

    def getProjectDependencies(self):
        # TODO: Detect whether this file depends on other LaTeX files in the
        #       project (e.g. base .tex files (subfiles), .cls or .sty files)
        pass

    def addRules(self, makefile):
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
        makefile.addRule(generatePdfRule(self.files['pdf'], self.getPath(),
                                         self.conf['build']))

###############################################################################
