import sys
from . import translate_file

if __name__ == '__main__':
    filename = sys.argv[1]
    output = translate_file(open(filename).readlines())
    print('\n'.join(output))
