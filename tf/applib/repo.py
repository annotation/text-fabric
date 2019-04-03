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
    APP_INFO,
    APP_EXPRESS,
    URL_GH,
    GH_BASE,
    EXPRESS_BASE,
    EXPRESS_INFO,
)
from ..core.helpers import console


class RepoData(object):

  # representing commit/release:

  # value '' means: latest
  # value None means: not relevant

  # in fromString:

  # latest means: latest release
  # hot means: latest commit

  @staticmethod
  def fromString(string):
    commit = None
    release = None
    if not string:
      commit = None
      release = None
    elif string == 'latest':
      commit = None
      release = ''
    elif string == 'hot':
      commit = ''
      release = None
    elif '.' in string or len(string) < 12:
      commit = None
      release = string
    else:
      commit = string
      release = None
    return (commit, release)

  @staticmethod
  def toString(commit, release):
    if commit and release:
      return f'r{release}=#{commit}'
    if commit:
      return f'#{commit}'
    if release:
      return f'r{release}'
    if commit is None and release is None:
      return 'unknown release or commit'
    if commit is None:
      return 'latest release'
    if release is None:
      return 'latest commit'
    return 'latest release or commit'

  def __init__(
      self,
      org,
      repo,
      relative,
      checkoutData,
      lgc,
      check,
      keep,
      withPaths,
      silent,
      version=None,
      isApp=False,
  ):
    self.org = org
    self.repo = repo
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
    self.dirPathTfd = f'{self.baseTfd}/{self.dataRelTfd}{versionRep}'
    self.dataPathTfd = f'{self.dataRelTfd}{versionRep}'
    self.filePathTfd = f'{self.dirPathTfd}/{APP_INFO if isApp else EXPRESS_INFO}'

    self.baseLgc = os.path.expanduser(GH_BASE)
    self.dataRelLgc = f'{org}/{repo}{relativeRep}'
    self.dirPathLgc = f'{self.baseLgc}/{self.dataRelLgc}{versionRep}'
    self.dataPathLgc = f'{self.dataRelLgc}{versionRep}'

    self.baseRep = (
        f'{GH_BASE}/{self.dataRelLgc}'
        if lgc else
        f'{EXPRESS_BASE}/{self.dataRelTfd}'
    ) + versionRep

    self.lgc = lgc
    self.check = check
    self.keep = keep
    self.withPaths = withPaths
    self.gh = None

    self.checkout = checkoutData

    self.commitOff = None
    self.releaseOff = None
    (self.commitChk, self.releaseChk) = self.fromString(self.checkout)
    self.commitOn = None
    self.releaseOn = None
    self.releaseCommitOn = None

    self.base = False

    if not self.lgc:
      self.readInfo()
    if not self.silent:
      offString = self.toString(self.commitOff, self.releaseOff)
      console(f'Offline data in {self.baseRep}:')
      console(f'\t{offString}')

    if self.check or not(self.commitOff or self.releaseOff):
      self.fetchInfo()
      if not self.silent:
        checkoutRep = self.toString(self.commitChk, self.releaseChk)
        console(f'Checkout data: {checkoutRep}')

  def makeSureLocal(self):
    if self.lgc:
      base = self.baseLgc
      dirPath = self.dirPathLgc
      self.base = base if os.path.exists(dirPath) else False
      return

    cOff = self.commitOff
    rOff = self.releaseOff
    cChk = self.commitChk
    rChk = self.releaseChk
    cOn = self.commitOn
    rOn = self.releaseOn

    isLocal = (
        cChk and cChk == cOff or
        cChk == '' and cOff and cOn == cOff
        or
        rChk and rChk == rOff or
        rChk == '' and rOff and rOn == rOff
    )
    isLocalStale = (
        cChk == '' and cOff and cOn != cOff
        or
        rChk == '' and rOff and rOn != rOff
    )
    noLocal = not (cOff or rOff)

    isOnline = (
        cChk and cChk == cOn or
        cChk == '' and cOn
        or
        rChk and rChk == rOn or
        rChk == '' and rOn
    )

    canFetch = self.repoOnline
    mayFetch = self.check or noLocal
    wantFetch = isLocalStale
    mustFetch = not isLocal
    willFetch = isOnline

    if mustFetch or (wantFetch and mayFetch):
      if canFetch and willFetch:
        self.base = self.baseTfd if self.downLoad(mustFetch, wantFetch, mayFetch) else False
      else:
        msg = (
            f'The requested data is not available online'
            if not willFetch else
            f'I cannot go online'
        )
        console(msg, error=True)
        self.base = False
    else:
      self.base = self.baseTfd
    if self.base:
      offString = self.toString(self.commitOff, self.releaseOff)
      console(f'Using data in {self.base}/{self.dataPath}:')
      console(f'\t{offString}')

  def download(self, must, want, may):
    cChk = self.commitChk
    rChk = self.releaseChk

    if rChk is not None:
      fetched = self.downloadRelease(rChk)
    elif cChk is not None:
      fetched = self.downloadCommit(cChk)

    if fetched:
      self.writeInfo()
    return False

  def downloadRelease(self, release):
    r = self.getReleaseObj(release)
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
      self.releaseOff = commit
    return fetched

  def downloadCommit(self, commit):
    c = self.getCommitObj(commit)
    if not c:
      return False
    commit = self.getCommitFromObj(c)
    return self.downloadDir(commit, exclude=r'\.tfx')

  def downloadZip(self, dataUrl, showErrors=True):
    silent = self.silent
    if not silent:
      console(f'\tdownloading {dataUrl} ... ')
    try:
      r = requests.get(dataUrl, allow_redirects=True)
      if not silent:
        console(f'\tunzipping ... ')
      zf = io.BytesIO(r.content)
    except Exception as e:
      if showErrors:
        console(f'\t{str(e)}\n\tcould not download {dataUrl}', error=True)
      return False

    if not silent:
      console(f'\tsaving data')

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
      if showErrors:
        console(f'\t{str(e)}\n\tcould not save data to {dest}', error=True)
      os.chdir(cwd)
      return False
    os.chdir(cwd)
    return True

  def downloadDir(self, commit, exclude=None):
    g = self.repoOnline
    if not g:
      return None

    dest = f'{self.dirPathTfd}'
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
          os.makedirs(f'{dest}/{thisPath}', exist_ok=True)
          _downloadDir(thisPath, level + 1)
        else:
          try:
            fileContent = g.get_git_blob(content.sha)
            fileData = base64.b64decode(fileContent.content)
            fileDest = f'{dest}/{thisPath}'
            with open(fileDest, 'wb') as fd:
              fd.write(fileData)
            if not silent:
              console('downloaded')
          except (GithubException, IOError) as exc:
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

  def getRelease(self, release):
    r = self.getReleaseObj(release)
    if not r:
      return None
    return self.getReleaseFromObj(r)

  def getCommit(self, commit):
    c = self.getCommitObj(commit)
    if not c:
      return None
    return self.getCommitFromObj(c)

  def getReleaseObj(self, release):
    g = self.repoOnline
    if not g:
      return None

    r = None
    msg = f' tagged "{release}"' if release else 's'

    try:
      r = g.get_release(release) if release else g.get_latest_release()
    except UnknownObjectException:
      console(f'\tno release{msg}', error=True)
    except Exception as exc:
      console(f'\tcannot find release{msg}: {exc}', error=True)
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
      result = self.getRelease(self.releaseChk)
      if result:
        (commit, release) = result
      elif self.releaseChk == '':
        commit = self.getCommit('')
    elif self.commitChk is not None:
      commit = self.getCommit(self.commitChk)
    self.commitOn = commit
    self.releaseOn = release

  def readInfo(self):
    string = ''
    if os.path.exists(self.filePathTfd):
      with open(self.filePathTfd) as f:
        for line in f:
          string = line.strip()
          (commit, release) = self.fromString(string)
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
      return good
    if not self.gh:
      try:
        self.gh = Github()
      except Exception as exc:
        console(exc, error=True)
        console('Cannot reach GitHub', error=True)
        return False
    try:
      self.repoOnline = self.gh.get_repo(f'{self.org}/{self.repo}')
    except (GithubException, IOError) as exc:
      console(exc, error=True)
      console('Cannot access online GitHub repo "{org}/{repo}"', error=True)
      return False
    return good
