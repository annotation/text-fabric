from tf.app import use
A = use('banks:clone', checkout='clone')
T = A.api.T
T.headingFromNode(100)
