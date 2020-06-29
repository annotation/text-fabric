from tf.core.data import Data
from tf.core.timestamp import Timestamp


@profile
def mem():
    path = '_temp/g_word_utf8.tf'
    tmObj = Timestamp()
    F = Data(path, tmObj)
    F._readDataBin()
    print(type(F))


if __name__ == '__main__':
    mem()
