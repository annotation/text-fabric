from ...core.generic import AttrDict
from ..web import Web
from ..kernel import makeTfKernel

from .settings import FEATURES
from .kernel import loadData
from .tables import filterS


class NER:
    def __init__(self, app, annoSet=""):
        kernelApi = makeTfKernel(app, app.appName)
        web = Web(kernelApi)
        self.web = web
        web.annoSet = annoSet
        web.toolData = AttrDict()
        loadData(web)

        templateData = AttrDict()
        self.templateData = templateData
        templateData.valselect = {feat: [] for feat in FEATURES}

    def findOccs(self, tokenStart, tokenEnd):
        web = self.web
        templateData = self.templateData

        templateData.tokenstart = tokenStart
        templateData.tokenend = tokenEnd
        templateData.valSelect = AttrDict()
        return filterS(web, templateData)
