import sys
from . import translate_file, BalanceAssertionTooComplicated

def main():
    filename = sys.argv[1]
    try:
        output = translate_file(open(filename).readlines())
        print('\n'.join(output))
        return 0
    except BalanceAssertionTooComplicated as e:
        print("Balance assertion with leftovers on line {}.".format(e.lineno))
        print("Because this is a syntactic translation, we can't represent this in beancount.")
        print("Please separate this into two transactions and try again.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
