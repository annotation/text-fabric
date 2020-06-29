from keyvi.dictionary import Dictionary


@profile
def mem():
    D = Dictionary("_temp/kv/g_word_utf8.txt")
    print(type(D))


if __name__ == '__main__':
    mem()
