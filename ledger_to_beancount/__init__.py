import decimal
from decimal import Decimal
import functools
import re

import dateutil.parser

START_DATE = '2010-01-01'


class BalanceAssertionTooComplicated(Exception):
    """Exception signalling a balance assertion with other postings.

    In the general case, this could be something like:

    2017-01-02 Balance assertion
        Assets:Cash   = $12
        Expenses:Cash

    Ledger supports this because it knows what the difference between
    Assets:Cash's current value and the target is, and can create a
    transaction from it. However, Beancount requires this to be split
    into a transaction and a balance assertion, and we have no way to
    know what the amount of the postings in the transaction are. (If
    we did, we would have reimplemented ledger.) Instead, complain and
    let the user sort it out.
    """
    def __init__(self, lineno):
        self.lineno = lineno


def starts_transaction(line):
    # Check if a line looks like a plausible beginning to a transaction
    if not line:  # blank lines never start transactions
        return False
    date = line
    if ' ' in line:
        (date, rest) = line.split(' ', 1)
        # Strip aux date
        date = date.split('=', 1)[0]
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
    BAD_CHARS = " ()'.&"
    for char in BAD_CHARS:
        account = account.replace(char, '')
    return re.sub(r'\:([\da-z])', r':X\1', account)


def strip_currency(amount):
    amount.strip()
    if amount[0] in ('$', '€', '₤'):
        amount = amount[1:]

    if ' ' in amount:
        (amount, currency) = amount.split()
    return amount


def parse_amount_and_units(amount):
    amount = amount.strip()
    if ' ' in amount:
        (amount, units) = amount.split(' ', 1)
        try:
            Decimal(amount)
        except decimal.InvalidOperation:
            units, amount = amount, units
        return (amount, units)


def identify_commodity(amount):
    amount = amount.strip()
    if re.match('\$|€|₤', amount):
        return False
    amount, commodity = parse_amount_and_units(amount)
    if commodity in ['USD', 'EUR', 'GBP', 'CAD']:
        return False

    return commodity


def translate_amount(amount):
    amount_re = r'(-?(\d*(\.\d+)?))'
    partial = functools.partial
    def replace_number(currency, match):
        amount = Decimal(match.group(1))
        return '{} {}'.format(str(amount), currency)
    amount = re.sub(r'\$\s?' + amount_re, partial(replace_number, 'USD'), amount)
    amount = re.sub(r'€\s?' + amount_re, partial(replace_number, 'EUR'), amount)
    amount = re.sub(r'₤\s?' + amount_re, partial(replace_number, 'GBP'), amount)

    return ' '.join(parse_amount_and_units(amount))


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
            rest = None
            account_end = None
            if '  ' in account:
                account_end = significant.index('  ')
            if account_end is not None:
                account = significant[:account_end]
                rest = significant[account_end:].strip()
            account = aliases.get(account, translate_account(account))
            accounts.add(account)

            # Check for balance assertion.
            # FIXME: We don't support balance assertions in the general case,
            # only as single-posting transactions, with zero as the addition.
            if rest and '=' in rest:
                in_balance_assertion = True

                non_commented_lines = [l for l in current_entry
                                       if not l.lstrip().startswith(';')]
                if len(non_commented_lines) != 1:
                    raise BalanceAssertionTooComplicated(lineno)

                (augment, balance) = rest.split('=')

                if augment and Decimal(strip_currency(augment.strip())) != 0.0:
                    # If the augment wasn't zero, it had to have come
                    # from/gone to another account.
                    raise BalanceAssertionTooComplicated(lineno)

                (date, _) = current_entry[0].split(' ', 1)

                balance_assertion = '{} balance {}   {}'.format(
                    date, account, translate_amount(balance.strip()))

                current_entry = [
                    reattach_comment(balance_assertion, comment)
                ] + current_entry[1:]

                continue

            elif rest and '@' in rest:
                # Could be a purchase or sale.
                (amount, price) = rest.split('@')
                # Translate commodity purchase/sales
                if identify_commodity(amount):
                    translated_amount = translate_amount(amount)
                    number, units = translated_amount.strip().split(' ')
                    if Decimal(number) > 0:
                        # A purchase!
                        format = '  {}        {} {{{}}}'
                    else:
                        # Correct spacing on sales at least
                        format = '  {}        {} @ {}'
                    posting = format.format(account, translated_amount.strip(),
                                            translate_amount(price).strip())
                    current_entry.append(reattach_comment(posting, comment))
                    continue
                # Don't do anything special with non-commodities
                # (currencies like $ or €)

            # Another posting.
            if in_balance_assertion:
                raise BalanceAssertionTooComplicated(lineno)

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
            narration = ''
            if ' ' in significant:
                date, narration = significant.split(' ', 1)
            date = date.split('=', 1)[0]
            date = dateutil.parser.parse(date)

            flag = '*'
            if narration[0] in ['!', '*']:
                flag = narration[0]
                narration = narration[1:].strip()

            new_transaction = "{date} {flag} \"{narration}\"".format(
                date=date.date(), flag=flag,
                narration=narration.replace('"', '\\"'))

            current_entry.append(reattach_comment(new_transaction, comment))

        elif significant.startswith('alias'):
            (alias_cmd, rest) = significant.split(' ', 1)
            (src, dest) = rest.split('=', 1)
            aliases[src.strip()] = translate_account(dest.strip())

        else:
            output.append(line)

    # EOF ends a transaction, whether there was a newline or not.
    if current_entry:
        output.extend(current_entry)

    # Prepend any accounts we've ever encountered
    account_openings = [
        '{} open {}'.format(START_DATE, a)
        for a in sorted(accounts)
    ]

    output = ['* Accounts'] + account_openings + ['* Transactions'] + output

    return output
