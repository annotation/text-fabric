import json
import os.path
import re
import ipykernel
import requests

from requests.compat import urljoin

from notebook.notebookapp import list_running_servers


def location():
  kernelId = re.search('kernel-(.*).json', ipykernel.connect.get_connection_file()).group(1)
  servers = list_running_servers()
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
        return (dirName, fileName, extension)
  return None
