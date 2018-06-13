VERSION = '2017'
DATABASE = '~/github/etcbc'
BHSA = f'bhsa/tf/{VERSION}'
PHONO = f'phono/tf/{VERSION}'
PARALLELS = f'parallels/tf/{VERSION}'

locations = [DATABASE]
modules = [BHSA, PHONO, PARALLELS]

host = 'localhost'
port = 18981
webport = 8001
