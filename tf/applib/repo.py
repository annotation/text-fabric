import sys
import os
import io
import re
from shutil import rmtree
import requests
import base64
from zipfile import ZipFile

from github import Github, GithubException, UnknownObjectException

from ..parameters import (
    APP_EXPRESS,
    URL_GH,
    GH_BASE,
    EXPRESS_BASE,
    EXPRESS_SYNC,
    EXPRESS_SYNC_LEGACY,
)
from ..core.helpers import console


class Checkout(object):

  @staticmethod
  def fromString(string):
    commit = None
    release = None
    local = None
    if not string:
      commit = ''
      release = ''
    elif string == 'latest':
      commit = None
      release = ''
    elif string == 'hot':
      commit = ''
      release = None
    elif string in {'local', 'clone'}:
      commit = None
      release = None
      local = string
    elif '.' in string or len(string) < 12:
      commit = None
      release = string
    else:
      commit = string
      release = None
    return (commit, release, local)

  @staticmethod
  def toString(commit, release, local):
    extra = ''
    if local:
      baseRep = GH_BASE if local == 'clone' else EXPRESS_BASE
      extra = f' offline under {baseRep}'
    if commit and release:
      result = f'r{release}=#{commit}'
    elif commit:
      result = f'#{commit}'
    elif release:
      result = f'r{release}'
    elif commit is None and release is None:
      result = f'unknown release or commit'
    elif commit is None:
      result = f'latest release'
    elif release is None:
      result = f'latest commit'
    else:
      result = f'latest release or commit'
    return f'{result}{extra}'

  def isClone(self):
    return self.local == 'clone'

  def isOffline(self):
    return self.local in {'clone', 'local'}

  def __init__(
      self,
      org,
      repo,
      relative,
      checkoutData,
      keep,
      withPaths,
      silent,
      version=None,
      isApp=False,
      label='data'
  ):
    self.label = label
    self.org = org
    self.repo = repo
    (self.commitChk, self.releaseChk, self.local) = self.fromString(checkoutData)
    clone = self.isClone()
    offline = self.isOffline()

    if isApp:
      parts = repo.split('-', maxsplit=1)
      self.app = parts[0] if len(parts) == 1 else parts[1]
    self.relative = relative
    self.version = version
    versionRep = f'/{version}' if version else ''
    relativeRep = f'/{relative}' if relative else ''
    relativeGh = f'/tree/master/{relative}' if relative else ''
    self.baseGh = f'{URL_GH}/{org}/{repo}{relativeGh}{versionRep}'
    self.dataDir = f'{relative}{versionRep}'

    self.baseTfd = os.path.expanduser(APP_EXPRESS if isApp else EXPRESS_BASE)
    orgRepo = self.app if isApp else f'{org}/{repo}'
    self.dataRelTfd = f'{orgRepo}{relativeRep}'
    self.dirPathSaveTfd = f'{self.baseTfd}/{orgRepo}'
    self.dirPathTfd = f'{self.baseTfd}/{self.dataRelTfd}{versionRep}'
    self.dataPathTfd = f'{self.dataRelTfd}{versionRep}'
    self.filePathTfd = f'{self.dirPathTfd}/{EXPRESS_SYNC}'

    self.baseLgc = os.path.expanduser(GH_BASE)
    self.dataRelLgc = f'{org}/{repo}{relativeRep}'
    self.dirPathLgc = f'{self.baseLgc}/{self.dataRelLgc}{versionRep}'
    self.dataPathLgc = f'{self.dataRelLgc}{versionRep}'

    self.baseRep = (
        f'{GH_BASE}/{self.dataRelLgc}'
        if clone else
        f'{EXPRESS_BASE}/{self.dataRelTfd}'
    ) + versionRep
    self.dataPath = self.dataPathLgc if clone else self.dataPathTfd

    self.keep = keep
    self.withPaths = withPaths
    self.ghConn = None

    self.commitOff = None
    self.releaseOff = None
    self.commitOn = None
    self.releaseOn = None
    self.releaseCommitOn = None

    self.silent = silent

    self.repoOnline = None
    self.localBase = False
    self.localDir = None

    if clone:
      self.commitOff = None
      self.releaseOff = None
      self.local = 'clone'
    else:
      self.fixInfo()
      self.readInfo()

    if not offline:
      self.connect()
      self.fetchInfo()

  def makeSureLocal(self):
    label = self.label
    offline = self.isOffline()
    clone = self.isClone()

    cOff = self.commitOff
    rOff = self.releaseOff
    cChk = self.commitChk
    rChk = self.releaseChk
    cOn = self.commitOn
    rOn = self.releaseOn

    silent = self.silent

    if offline:
      if clone:
        localBase = self.baseLgc
        dirPath = self.dirPathLgc
        self.localBase = localBase if os.path.exists(dirPath) else False
      else:
        localBase = self.baseTfd
        self.localBase = (
            localBase if (
                cChk and cChk == cOff or
                cChk is None and cOff or
                rChk and rChk == rOff or
                rChk is None and rOff
            ) else
            False
        )
      if not self.localBase:
        console(f'The requested {label} is not available offline', error=True)
    else:
      isLocal = (
          cChk and cChk == cOff or
          cChk == '' and cOff
          or
          rChk and rChk == rOff or
          rChk == '' and rOff
      )
      isLocalStale = (
          cChk == '' and cOff and cOn != cOff
          or
          rChk == '' and rOff and rOn != rOff
      )

      isOnline = (
          cChk and cChk == cOn or
          cChk == '' and cOn
          or
          rChk and rChk == rOn or
          rChk == '' and rOn
      )

      canOnline = self.repoOnline

      if isLocal and not isLocalStale:
        self.localBase = self.baseTfd
      else:
        if not silent:
          console(f'The requested {label} is not available offline')
        if not canOnline:
          console(f'No online connection', error=True)
        elif not isOnline:
          console(f'The requested {label} is not available online', error=True)
        else:
          self.localBase = self.baseTfd if self.download() else False

    if self.localBase:
      self.localBase = self.dataPath
      state = (
          'requested' if cChk or rChk else
          'latest release' if rChk == '' and self.releaseOff else
          'latest commit' if cChk == '' and self.commitOff else
          'latest' if cChk == '' or rChk == '' else
          'local - without online check' if self.local == 'local' else
          'local github - without online check' if self.local == 'clone' else
          'for whatever reason'
      )
      offString = self.toString(self.commitOff, self.releaseOff, self.local)
      if not silent:
        console(f'Using {label} in {self.localBase}/{self.localDir}:')
        console(f'\t{offString} ({state})')

  def download(self):
    cChk = self.commitChk
    rChk = self.releaseChk

    fetched = False
    if rChk is not None:
      fetched = self.downloadRelease(rChk, showErrors=cChk is None)
    if not fetched and cChk is not None:
      fetched = self.downloadCommit(cChk)

    if fetched:
      self.writeInfo()
    return fetched

  def downloadRelease(self, release, showErrors=True):
    r = self.getReleaseObj(release, showErrors=showErrors)
    if not r:
      return False
    (commit, release) = self.getReleaseFromObj(r)

    assets = None
    try:
      assets = r.get_assets()
    except Exception:
      pass
    assetUrl = None
    versionRep3 = f'-{self.version}' if self.version else ''
    relativeFlat = self.relative.replace('/', '-')
    dataFile = f'{relativeFlat}{versionRep3}.zip'
    if assets and assets.totalCount > 0:
      for asset in assets:
        if asset.name == dataFile:
          assetUrl = asset.browser_download_url
          break
    fetched = False
    if assetUrl:
      fetched = self.downloadZip(assetUrl, showErrors=False)
    if not fetched:
      fetched = self.downloadCommit(commit)
    if fetched:
      self.commitOff = commit
      self.releaseOff = release
    return fetched

  def downloadCommit(self, commit):
    c = self.getCommitObj(commit)
    if not c:
      return False
    commit = self.getCommitFromObj(c)
    fetched = self.downloadDir(commit, exclude=r'\.tfx')
    if fetched:
      self.commitOff = commit
      self.releaseOff = None
    return fetched

  def downloadZip(self, dataUrl, showErrors=True):
    label = self.label
    silent = self.silent
    if not silent:
      console(f'\tdownloading {dataUrl} ... ')
    try:
      r = requests.get(dataUrl, allow_redirects=True)
      if not silent:
        console(f'\tunzipping ... ')
      zf = io.BytesIO(r.content)
    except Exception as e:
      if showErrors or not silent:
        console(f'\t{str(e)}\n\tcould not download {dataUrl}', error=showErrors)
      return False

    if not silent:
      console(f'\tsaving {label}')

    cwd = os.getcwd()
    try:
      z = ZipFile(zf)
      dest = self.dirPathTfd
      if not self.keep:
        if os.path.exists(dest):
          rmtree(dest)
      os.makedirs(dest, exist_ok=True)
      os.chdir(dest)
      if self.withPaths:
        z.extractall()
        if os.path.exists('__MACOSX'):
          rmtree('__MACOSX')
      else:
        for zInfo in z.infolist():
          if zInfo.filename[-1] == '/':
            continue
          if zInfo.filename.startswith('__MACOS'):
            continue
          zInfo.filename = os.path.basename(zInfo.filename)
          z.extract(zInfo)
    except Exception as e:
      if showErrors or not silent:
        console(f'\t{str(e)}\n\tcould not save {label} to {dest}', error=showErrors)
      os.chdir(cwd)
      return False
    os.chdir(cwd)
    return True

  def downloadDir(self, commit, exclude=None):
    g = self.repoOnline
    if not g:
      return None

    dest = f'{self.dirPathTfd}'
    destSave = f'{self.dirPathSaveTfd}'
    if not self.keep:
      if os.path.exists(dest):
        rmtree(dest)
    os.makedirs(dest, exist_ok=True)

    excludeRe = re.compile(exclude) if exclude else None
    silent = self.silent

    good = True

    def _downloadDir(subPath, level=0):
      nonlocal good
      lead = '\t' * level
      contents = g.get_dir_contents(subPath, ref=commit)
      for content in contents:
        thisPath = content.path
        if not silent:
          sys.stdout.write(f'\t{lead}{thisPath}...')
        if exclude and excludeRe.search(thisPath):
          if not silent:
            console('excluded')
          continue
        if content.type == 'dir':
          if not silent:
            console('directory')
          os.makedirs(f'{destSave}/{thisPath}', exist_ok=True)
          _downloadDir(thisPath, level + 1)
        else:
          try:
            fileContent = g.get_git_blob(content.sha)
            fileData = base64.b64decode(fileContent.content)
            fileDest = f'{destSave}/{thisPath}'
            with open(fileDest, 'wb') as fd:
              fd.write(fileData)
            if not silent:
              console('downloaded')
          except (GithubException, IOError) as exc:
            if not silent:
              console('error')
            console(f'{lead}{exc}', error=True)
            good = False

    _downloadDir(self.dataDir, 0)

    if good:
      if not silent:
        console('\tOK')
    else:
      console('\tDone. There were errors', error=True)

    return good

  def getRelease(self, release, showErrors=True):
    r = self.getReleaseObj(release, showErrors=showErrors)
    if not r:
      return None
    return self.getReleaseFromObj(r)

  def getCommit(self, commit):
    c = self.getCommitObj(commit)
    if not c:
      return None
    return self.getCommitFromObj(c)

  def getReleaseObj(self, release, showErrors=True):
    g = self.repoOnline
    if not g:
      return None

    r = None
    msg = f' tagged "{release}"' if release else 's'

    try:
      r = g.get_release(release) if release else g.get_latest_release()
    except UnknownObjectException:
      if showErrors or not self.silent:
        console(f'\tno release{msg}', error=showErrors)
    except Exception as exc:
      if showErrors or not self.silent:
        console(f'\tcannot find release{msg}: {exc}', error=showErrors)
    return r

  def getCommitObj(self, commit):
    g = self.repoOnline
    if not g:
      return None

    c = None
    msg = f' with hash "{commit}"' if commit else 's'

    try:
      cs = g.get_commits(sha=commit) if commit else g.get_commits()
      if cs.totalCount:
        c = cs[0]
      else:
        console(f'\tno commit{msg}', error=True)
    except Exception as exc:
      console(f'\tcannot find commit{msg}: {exc}', error=True)
    return c

  def getReleaseFromObj(self, r):
    g = self.repoOnline
    if not g:
      return None
    release = r.tag_name
    ref = g.get_git_ref(f'tags/{release}')
    commit = ref.object.sha
    return (commit, release)

  def getCommitFromObj(self, c):
    g = self.repoOnline
    if not g:
      return None
    return c.sha

  def fetchInfo(self):
    commit = None
    release = None
    if self.releaseChk is not None:
      result = self.getRelease(self.releaseChk, showErrors=self.commitChk is None)
      if result:
        (commit, release) = result
      elif self.commitChk is not None:
        commit = self.getCommit('')
    elif self.commitChk is not None:
      commit = self.getCommit(self.commitChk)
    self.commitOn = commit
    self.releaseOn = release

  def fixInfo(self):
    sDir = self.dirPathTfd
    if not os.path.exists(sDir):
      return
    for sFile in EXPRESS_SYNC_LEGACY:
      sPath = f'{sDir}/{sFile}'
      if os.path.exists(sPath):
        goodPath = f'{sDir}/{EXPRESS_SYNC}'
        if os.path.exists(goodPath):
          os.remove(sPath)
        else:
          os.rename(sPath, goodPath)

  def readInfo(self):
    if os.path.exists(self.filePathTfd):
      with open(self.filePathTfd) as f:
        for line in f:
          string = line.strip()
          (commit, release, local) = self.fromString(string)
          if commit:
            self.commitOff = commit
          if release:
            self.releaseOff = release

  def writeInfo(self):
    if not os.path.exists(self.dirPathTfd):
      os.makedirs(self.dirPathTfd, exist_ok=True)
    with open(self.filePathTfd, 'w') as f:
      if self.releaseOff:
        f.write(f'{self.releaseOff}\n')
      if self.commitOff:
        f.write(f'{self.commitOff}\n')

  def connect(self):
    if self.repoOnline:
      return True
    if not self.ghConn:
      try:
        ghClient = os.environ.get('GHCLIENT', None)
        ghSecret = os.environ.get('GHSECRET', None)
        self.ghConn = Github(client_id=ghClient, client_secret=ghSecret)
      except Exception as exc:
        console(exc, error=True)
        console('Cannot reach GitHub', error=True)
        return False
    try:
      self.repoOnline = self.ghConn.get_repo(f'{self.org}/{self.repo}')
    except (GithubException, IOError) as exc:
      console(exc, error=True)
      console('Cannot access online GitHub repo "{org}/{repo}"', error=True)
      return False
    return True


def checkoutRepo(
    org='annotation',
    repo='tutorials',
    folder='text-fabric/examples/banks/tf',
    version='',
    checkout='',
    withPaths=True,
    keep=True,
    silent=False,
    label='data',
):
  rData = Checkout(
      org,
      repo,
      folder,
      checkout,
      keep,
      withPaths,
      silent,
      version=version,
      label=label,
  )
  rData.makeSureLocal()
  return (
      rData.commitOff,
      rData.releaseOff,
      rData.local,
      rData.localBase,
      rData.localDir,
  ) if rData.localBase else (None, None, False, False)
