from .data import Data


from ...core.generic import AttrDict
from ...core.files import (
    fileExists,
    initTree,
    dirExists,
    dirContents,
    dirMake,
    dirCopy,
    dirRemove,
    dirMove,
)

from .settings import ERROR


class Sets(Data):
    def __init__(self, data=None):
        super().__init__(data=data)
        settings = self.settings
        entitySet = settings.entitySet

        self.annoSet = ""
        self.annoSetRep = entitySet

        annoDir = self.annoDir
        self.setNames = set(dirContents(annoDir)[1])

    def setSet(self, newAnnoSet):
        settings = self.settings
        entitySet = settings.entitySet
        browse = self.browse

        if not browse:
            self.loadData()

        data = self.data
        setNames = self.setNames
        setsData = data.sets
        annoSet = self.annoSet
        annoDir = self.annoDir
        newSetDir = f"{annoDir}/{newAnnoSet}"

        if newAnnoSet and (newAnnoSet not in setNames or not dirExists(newSetDir)):
            initTree(newSetDir)
            setNames.add(newAnnoSet)

        if newAnnoSet != annoSet:
            annoSet = newAnnoSet
            self.annoSet = annoSet
            self.annoSetRep = annoSet if annoSet else entitySet
            self.loadData()

        if not browse:
            annoSetRep = self.annoSetRep
            entities = setsData[annoSet].entities
            nEntities = len(entities)
            plural = "" if nEntities == 1 else "s"
            self.console(
                f"Annotation set {annoSetRep} has {nEntities} annotation{plural}"
            )

    def resetSet(self):
        settings = self.settings
        annoSet = self.annoSet
        entitySet = settings.entitySet

        if not annoSet:
            self.console(f"Resetting the {entitySet} has no effect")
            return

        browse = self.browse

        data = self.data
        setsData = data.sets
        annoDir = self.annoDir
        setDir = f"{annoDir}/{annoSet}"

        initTree(setDir, fresh=True, gentle=True)
        self.loadData()

        if not browse:
            annoSetRep = self.annoSetRep
            entities = setsData[annoSet].entities
            nEntities = len(entities)
            plural = "" if nEntities == 1 else "s"
            self.console(
                f"Annotation set {annoSetRep} has {nEntities} annotation{plural}"
            )

    def getSetData(self):
        data = self.data
        setsData = data.sets
        annoSet = self.annoSet
        setData = setsData.setdefault(annoSet, AttrDict())
        return setData

    def getSetEntities(self):
        return self.getSetData().entities

    def setDel(self, delSet):
        data = self.data
        setNames = self.setNames
        setsData = data.sets
        annoDir = self.annoDir
        annoPath = f"{annoDir}/{delSet}"

        messages = []

        dirRemove(annoPath)

        if dirExists(annoPath):
            messages.append((ERROR, f"""Could not remove {delSet}"""))
        else:
            setNames.discard(delSet)
            del setsData[delSet]
            self.annoSet = ""

        return messages

    def setDup(self, dupSet):
        data = self.data
        setNames = self.setNames
        setsData = data.sets
        annoSet = self.annoSet
        annoDir = self.annoDir
        annoPath = f"{annoDir}/{dupSet}"

        messages = []

        if dupSet in setNames:
            messages.append((ERROR, f"""Set {dupSet} already exists"""))
        else:
            if annoSet:
                if not dirCopy(
                    f"{annoDir}/{annoSet}",
                    annoPath,
                    noclobber=True,
                ):
                    messages.append(
                        (ERROR, f"""Could not copy {annoSet} to {dupSet}""")
                    )
                else:
                    setNames.add(dupSet)
                    setsData[dupSet] = setsData[annoSet]
                    self.annoSet = dupSet
            else:
                dataFile = f"{annoPath}/entities.tsv"

                if fileExists(dataFile):
                    messages.append((ERROR, f"""Set {dupSet} already exists"""))
                else:
                    dirMake(annoPath)
                    self.saveEntitiesAs(dataFile)
                    setNames.add(dupSet)
                    setsData[dupSet] = setsData[annoSet]
                    self.annoSet = dupSet

        return messages

    def setMove(self, moveSet):
        data = self.data
        setNames = self.setNames
        setsData = data.sets
        annoSet = self.annoSet
        annoDir = self.annoDir
        annoPath = f"{annoDir}/{moveSet}"

        messages = []

        if dirExists(annoPath):
            messages.append((ERROR, f"""Set {moveSet} already exists"""))
        else:
            if not dirMove(f"{annoDir}/{annoSet}", annoPath):
                messages.append(
                    (
                        ERROR,
                        f"""Could not rename {annoSet} to {moveSet}""",
                    )
                )
            else:
                setNames.add(moveSet)
                setNames.discard(annoSet)
                setsData[moveSet] = setsData[annoSet]
                del setsData[annoSet]
                self.annoSet = moveSet

        return messages
