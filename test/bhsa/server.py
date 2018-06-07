from tf.service import makeTfServer

PORT = 18981

VERSION = '2017'
DATABASE = '~/github/etcbc'
BHSA = f'bhsa/tf/{VERSION}'
PHONO = f'phono/tf/{VERSION}'
PARALLELS = f'parallels/tf/{VERSION}'
locations = [DATABASE]
modules = [BHSA, PHONO, PARALLELS]

makeTfServer(locations, modules, PORT).start()
