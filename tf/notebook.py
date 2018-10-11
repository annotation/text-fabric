import json
import os.path
import re
import ipykernel
import requests

from requests.compat import urljoin

from notebook.notebookapp import list_running_servers


def repoLocation(cwd):
  cwdPat = re.compile(f'^.*/github/([^/]+)/([^/]+)((?:/.+)?)$', re.I)
  cwdRel = cwdPat.findall(cwd)
  # org, repo, path
  return cwdRel[0] if cwdRel else None


def location(name, cwd):
  repoLoc = repoLocation(cwd)
  if not repoLoc:
    return None

  try:
    kernelId = re.search('kernel-(.*).json', ipykernel.connect.get_connection_file()).group(1)
  except Exception:
    return None
  servers = list_running_servers()

  found = None
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

  if name is not None:
    fileName = name
  if not found:
    return None

  return found + repoLoc
