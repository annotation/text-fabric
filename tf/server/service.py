import rpyc
from .data import makeTfServer
from .common import getParam, getConfig


def main():
  dataSource = getParam(interactive=True)
  if dataSource is not None:
    config = getConfig(dataSource)
    if config is not None:
      service = makeTfServer(dataSource, config.locations, config.modules, config.port)
      if service:
        service.start()


def makeTfConnection(host, port):
  class TfConnection(object):
    def connect(self):
      connection = rpyc.connect(host, port)
      self.connection = connection
      return connection.root

  return TfConnection()


if __name__ == "__main__":
    main()
