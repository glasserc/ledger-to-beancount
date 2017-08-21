from decimal import Decimal
import re

import dateutil.parser

START_DATE = '2010-01-01'


def starts_transaction(line):
    # Check if a line looks like a plausible beginning to a transaction
    if not line:  # blank lines never start transactions
        return False
    date = line
    if ' ' in line:
        (date, rest) = line.split(' ', 1)
    try:
        date = dateutil.parser.parse(date)
    except ValueError:
        return False

    return True


def trim_comment(line):
    """Remove any comment and its spacing from the line."""
    if ';' not in line:
        return (line, None)

    comment_start = line.index(';')
    before_comment = line[:comment_start]
    spaces_before_comment = len(before_comment) - len(before_comment.rstrip())
    comment = line[comment_start:]
    return (before_comment.rstrip(), spaces_before_comment * ' ' + comment)


def reattach_comment(line, comment):
    if not comment:
        return line

    return line + comment


def translate_account(account):
    # FIXME: we should actually use a whitelist here
    BAD_CHARS = " ()'."
    for char in BAD_CHARS:
        account = account.replace(char, '')
    return re.sub(r'\:(\d)', r':X\1', account)


def strip_currency(amount):
    amount.strip()
    if amount[0] in ('$', '€', '₤'):
        amount = amount[1:]

    if ' ' in amount:
        (amount, currency) = amount.split()
    return amount


def translate_amount(amount):
    amount_re = r'(-?\d*(\.\d+)?)'
    amount = re.sub(r'\$' + amount_re, '\\1 USD', amount)
    amount = re.sub(r'€' + amount_re, '\\1 EUR', amount)
    amount = re.sub(r'₤' + amount_re, '\\1 GBP', amount)
    return amount


def translate_file(file_lines):
    accounts = set()
    aliases = {}

    output = []
    current_entry = []
    in_balance_assertion = False

    for lineno, line in enumerate(file_lines):
        if line and line[-1] == '\n':
            line = line[:-1]

        significant = line.strip()
        (significant, comment) = trim_comment(line)
        significant = significant.strip()

        if current_entry and line.startswith(' '):
            # Continuation of current entry.
            line = '  ' + line.lstrip()
            if not significant:
                current_entry.append(line)
                continue

            account = significant
            if '  ' in account:
                account = significant[:significant.find('  ')]
            account = aliases.get(account, translate_account(account))
            accounts.add(account)
            rest = None
            if '  ' in significant:
                rest = significant[significant.find('  '):].strip()

            # Check for balance assertion.
            # FIXME: We don't support balance assertions in the general case,
            # only as single-posting transactions, with zero as the addition.
            if rest and '=' in rest:
                in_balance_assertion = True
                assert len(current_entry) == 1

                (augment, balance) = rest.split('=')

                if augment:
                    assert Decimal(strip_currency(augment.strip())) == 0.0

                (date, _) = current_entry[0].split(' ', 1)

                balance_assertion = '{} balance {}   {}'.format(
                    date, account, translate_amount(balance.strip()))

                current_entry = [
                    reattach_comment(balance_assertion, comment)
                ]

            # Check for posting -- transform money
            else:
                if in_balance_assertion:
                    print("Balance assertion with leftovers on line {}.".format(lineno))
                    print("Because this is a syntactic translation, we can't represent this in beancount.")
                    print("Please separate this into two transactions and try again.")
                    return 1

                if rest:
                    posting = '  {}        {}'.format(account, translate_amount(rest))
                else:
                    posting = '  {}'.format(account)

                current_entry.append(reattach_comment(posting, comment))

            # Since this continued an existing entry, skip to the next line.
            continue

        if current_entry:
            output.extend(current_entry)
            current_entry = []
            in_balance_assertion = False

        if starts_transaction(significant):
            date = significant
            rest = ''
            if ' ' in significant:
                date, rest = significant.split(' ', 1)
            date = dateutil.parser.parse(date)
            new_transaction = "{} * \"{}\"".format(date.date(), rest.replace('"', '\\"'))
            current_entry.append(reattach_comment(new_transaction, comment))

        elif significant.startswith('alias'):
            (alias_cmd, rest) = significant.split(' ', 1)
            (src, dest) = rest.split('=', 1)
            aliases[src.strip()] = translate_account(dest.strip())

        else:
            output.append(line)

    # Prepend any accounts we've ever encountered
    account_openings = [
        '{} open {}'.format(START_DATE, a)
        for a in sorted(accounts)
    ]

    output = ['* Accounts'] + account_openings + ['* Transactions'] + output

    return output
