from .data import makeTfServer
from .common import getParam, getConfig


def tfService():
  dataSource = getParam()
  if dataSource is not None:
    config = getConfig(dataSource)
    if config is not None:
      service = makeTfServer(dataSource, config.locations, config.modules, config.port)
      if service:
        service.start()


if __name__ == "__main__":
    tfService()
