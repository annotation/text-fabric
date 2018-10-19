import json
import os.path
import re
import ipykernel
import requests

from requests.compat import urljoin

from notebook.notebookapp import list_running_servers

from tf.apphelpers import URL_GH, URL_NB


def repoLocation(cwd):
  cwdPat = re.compile(f'^.*/github/([^/]+)/([^/]+)((?:/.+)?)$', re.I)
  cwdRel = cwdPat.findall(cwd)
  if not cwdRel:
    return None
  # org, repo, path
  (org, repo, path) = cwdRel[0]
  onlineTail = (f'{org}/{repo}' f'/blob/master{path}')
  nbUrl = f'{URL_NB}/{onlineTail}'
  ghUrl = f'{URL_GH}/{onlineTail}'
  return (org, repo, path, nbUrl, ghUrl)


def location(cwd, name):
  repoLoc = repoLocation(cwd)
  if name is not None:
     return (('', name, '.ipynb'), repoLoc)

  hasKernel = False
  try:
    kernelId = re.search('kernel-(.*).json', ipykernel.connect.get_connection_file()).group(1)
    hasKernel = True
  except Exception:
    pass

  found = None

  try:
    servers = list_running_servers()
    if hasKernel:
      for ss in servers:
          response = requests.get(
              urljoin(ss['url'], 'api/sessions'), params={'token': ss.get('token', '')}
          )
          for nn in json.loads(response.text):
            if nn['kernel']['id'] == kernelId:
              relPath = nn['notebook']['path']
              absPath = os.path.join(ss['notebook_dir'], relPath)
              (dirName, filePart) = os.path.split(absPath)
              (fileName, extension) = os.path.splitext(filePart)
              found = (dirName, fileName, extension)
              break
  except Exception:
    print('Cannot determine the name of this notebook')
    print("Work around: call me with a self-chosen name: name='xxx'")

  return (found, repoLoc)
