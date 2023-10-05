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

from .settings import ERROR, ENT_SET


class Sets(Data):
    def __init__(self):
        super().__init__()

        self.annoSet = ""
        self.annoSetRep = ENT_SET

        annoDir = self.annoDir
        self.setNames = set(dirContents(annoDir)[1])

    def setSet(self, newAnnoSet):
        browse = self.browse
        data = self.data
        setNames = self.setNames
        setsData = data.sets
        annoSet = self.annoSet
        annoDir = self.annoDir

        if newAnnoSet and newAnnoSet not in setNames:
            initTree(f"{annoDir}/{newAnnoSet}", fresh=False)
            setNames.add(newAnnoSet)

        if newAnnoSet != annoSet:
            annoSet = newAnnoSet
            self.annoSet = annoSet
            self.annoSetRep = annoSet if annoSet else ENT_SET
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
