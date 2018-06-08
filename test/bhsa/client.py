import os
from glob import glob

from tf.service import makeTfConnection

HOST = 'localhost'
PORT = 18981

print(f'Connecting to TF service at port {PORT}')

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

    # Here we call the TF server
    # api.search(query, context) here
    # calls S.search(query, withContext=context)
    # on the server.
    # Hint: look up the S.search() method
    # and note the withContext argument.

    (results, context) = api.search(query, True)

    # The results are still on the server
    # The next two statements fetch them physically
    # It seems that you can do as if the data is already
    # fetched, but there are glitches:
    # none of the named methods of a dict work with
    # these shadowed objects.
    # Must be a bug in RPYC.
    # Hence, we fetch the results in local datastructures.

    # results = tuple(results)
    # context = {feature: context[feature] for feature in context}

    headResults = '\n'.join(f'{r}' for r in results[0:10])
    print(f'{len(results)} results.\n{headResults}')
    for (feature, values) in context.items():
        showValues = values[0] if type(values) is tuple else values
        if len(showValues):
            print(f'{feature:>15} : {len(showValues):>7} values')
