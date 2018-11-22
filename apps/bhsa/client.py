import os
import pickle
from glob import glob

from tf.server.kernel import makeTfConnection

HOST = 'localhost'
PORT = 18981

print(f'Connecting to TF kernel at port {PORT}')

TF = makeTfConnection(HOST, PORT)
api = TF.connect()

queries = [(f[5:-4], f) for f in sorted(glob('query[0-9]*.txt'))]

queriesStr = '\n\t'.join(f'{q[0]} = {q[1]}' for q in queries)

answer = True

while answer:
    prompt = f'Which query shall I run?\n\t{queriesStr}\n> '
    answer = input(prompt)
    if not answer:
        break
    queryFile = f'query{answer}.txt'
    if not os.path.exists(queryFile):
        print(f'No file {queryFile} . Try again.')
        continue
    with open(queryFile) as qh:
        query = qh.read()

    print('Call TF kernel')
    (csvs, context) = api.csvs(
        query,
        '',
        '',
        False,
        None,
    )
    print('TF kernel has answered')
    print('Fetching CSV results')
    csvs = pickle.loads(csvs)
    for (csv, data) in csvs:
      print(f'{csv} ...')
      i = 0
      for tup in data:
        i += 1
      print(f'{i} tuples')
    print('CSVS done')
    print('Fetching context')
    context = pickle.loads(context)
    i = 0
    for tup in context:
      i += 1
    print(f'{i} tuples')
