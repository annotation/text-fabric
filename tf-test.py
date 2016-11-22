from tf.read import readFeature

testDir = 'tests'

def test_monads():
    result = readFeature('{}/{}.tf'.format('tests', 'monads'))

    if result == None:
        print('There were errors')
    else:
        (isEdge, metaData, data) = result
        label = 'edge' if isEdge else 'node'
        print('{} feature\n{}\nData: {} {}s'.format(
            label,
            '\n'.join('{:<20}: {}'.format(*x) for x in sorted(metaData.items())),
            len(data),
            label,
        ))

test_monads()
