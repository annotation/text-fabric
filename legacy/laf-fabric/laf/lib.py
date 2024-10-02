import array
from itertools import zip_longest

def grouper(iterable, n, fillvalue=None):
    '''Collect data into fixed-length chunks or blocks

    grouper([1,2,3,4,5], 2, 0) --> [1,2] [3,4] [5,0]
    '''
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def arrayify(source_list):
    dest_array = array.array('I')
    dests_array = array.array('I')
    j = 0
    for i in range(len(source_list)):
        items = source_list[i]
        dest_array.append(j)
        dests_array.append(len(items))
        dests_array.extend(items)
        j += 1 + len(items)
    return (dest_array, dests_array)

def make_inverse(mapping): return dict((y,x) for (x,y) in mapping.items())
def make_array_inverse(arraylist): return dict((x,n) for (n,x) in enumerate(arraylist))

