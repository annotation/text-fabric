"""Annotation set management.

Annotation sets contain the annotations that the user generates by using
the tool.

To see how this fits among all the modules of this package, see
`tf.browser.ner.annotate` .
"""

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
        """Methods to create, duplicate, rename and delete annotation sets.

        Annotation sets have names, given by the user.

        There is one special annotation set, whose name is the empty string,
        and whose content are the pre-existing entities, i.e. the entities that
        are present in the TF data as nodes and features.

        There is always one current annotation set, whose data is loaded into
        memory.

        Parameters
        ----------
        data: object, optional None
            Entity data to start with.
            If None, a fresh data store will be created by a parent class (Data).
        """
        super().__init__(data=data)
        if not self.properlySetup:
            return

        settings = self.settings
        entitySet = settings.entitySet

        self.annoSet = ""
        """The current annotation set."""

        self.annoSetRep = entitySet
        """The name representation of the current annotation set."""

        annoDir = self.annoDir
        self.setNames = set(dirContents(annoDir)[1])
        """The set of names of annotation sets that are present on the file system."""

    def getSetData(self):
        """Deliver the data of the current set.
        """
        data = self.data
        setsData = data.sets
        annoSet = self.annoSet
        setData = setsData.setdefault(annoSet, AttrDict())
        return setData

    def setSet(self, newAnnoSet):
        """Switch to a named annotation set.

        If the new set does not exist, it will be created.
        After the switch, the data of the new set will be loaded into memory.

        Parameters
        ----------
        newAnnoSet: string
            The name of the new annotation set to switch to.
        """
        if not self.properlySetup:
            return

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
        """Clear the current annotation set.

        The special set `""` cannot be reset, because it is read-only.
        """
        if not self.properlySetup:
            return

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

    def setDup(self, dupSet):
        """Duplicates the current set to a set with a new name.

        !!! hint "The special set can be duplicated"
            After duplication of the special read-only set, the duplicate
            copy is modifiable.
            In this way you can make corrections to the set of pre-existing,
            tool-generated annotations.

        The current set changes to the result of the duplication.

        Parameters
        ----------
        dupSet: string
            The name of new set that is the result of the duplication.
        """
        if not self.properlySetup:
            return []

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

    def setDel(self, delSet):
        """Remove a named set.

        If the removed set happens to be the current set, the current set changes
        to the special set named `""`.

        Parameters
        ----------
        delSet: string
            The name of the set to be removed.
            It is not allowed to remove the special set named `""`.
        """
        if not self.properlySetup:
            return []

        messages = []

        if delSet == "":
            messages.append("""Cannot remove set "" because it is read-only""")
            return messages

        data = self.data
        setNames = self.setNames
        setsData = data.sets
        annoDir = self.annoDir
        annoPath = f"{annoDir}/{delSet}"

        dirRemove(annoPath)

        if dirExists(annoPath):
            messages.append((ERROR, f"""Could not remove {delSet}"""))
        else:
            setNames.discard(delSet)
            del setsData[delSet]
            if self.annoSet == delSet:
                self.annoSet = ""

        return messages

    def setMove(self, moveSet):
        """Renames a named set.

        The current set changes to the renamed set.
        It is not possible to rename the special set named `""`.
        It is also forbidden to rename another set to the special set.

        Parameters
        ----------
        moveSet: string
            The new name of the current set.
        """
        if not self.properlySetup:
            return []

        messages = []

        if moveSet == "":
            messages.append("""Cannot rename a set to "".""")
            return messages

        annoSet = self.annoSet

        if annoSet == "":
            messages.append("""Cannot rename set "".""")
            return messages

        data = self.data
        setNames = self.setNames
        setsData = data.sets
        annoDir = self.annoDir
        annoPath = f"{annoDir}/{moveSet}"

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
