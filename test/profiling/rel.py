from tf.app import use

query = '''
p:phrase
    =: wFirst:word
    wLast:word
    :=

wGap:word
wFirst < wGap
wLast > wGap

p || wGap

v:verse

v [[ wFirst
v [[ wGap
'''

A = use('bhsa:clone', checkout='clone')
results = A.search(query)
