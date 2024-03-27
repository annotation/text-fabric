from timeit import timeit
from multiprocessing import shared_memory

def test(size):
    data = [1 for i in range(size)]
    dataM = shared_memory.ShareableList(data, name=f"data{size}")
    print(f'''{timeit("max(data)", globals=locals(), number=1):>.3e}''')
    print(f'''{timeit("max(dataM)", globals=locals(), number=1):>.3e}''')
    

test(1000)
test(10000)
test(100000)

##########################
# 3.8.3
# 
# 2.149e-05     3.201e-02
# 1.845e-04     1.914e+00
# 1.428e-03     1.838e+02
# 
##########################
# 3.9.0b3
# 
# 2.357e-05     4.543e-03
# 2.026e-04     3.832e-02
# 1.526e-03     3.016e-01 