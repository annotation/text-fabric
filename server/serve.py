from subprocess import Popen, run

from serveTf import getParam

dataSource = getParam()
if dataSource is not None:
  pData = Popen(['python3', 'serveTf.py', dataSource])
  try:
    run(['python3', 'index.py', dataSource])
  except KeyboardInterrupt:
    print('Terminated web server')
  pData.terminate()
  print('Terminated TF data server')
