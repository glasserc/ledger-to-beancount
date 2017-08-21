import pytest

from ledger_to_beancount import translate_file, BalanceAssertionTooComplicated


def from_triple_quoted_string(s, append_newlines=False):
    if s[0] == '\n':
        s = s[1:]
    lines = s.split('\n')
    indentation = len(lines[0]) - len(lines[0].lstrip())
    lines = [line[indentation:] for line in lines]

    if append_newlines:
        lines = [line + '\n' for line in lines]

    return lines


def test_comments_are_copied_through():
    input = from_triple_quoted_string("""
    ; Intro comment
    ;; Multi-semicolon comment
        ;; Pre-spaced comment
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    * Transactions
    ; Intro comment
    ;; Multi-semicolon comment
        ;; Pre-spaced comment
    """)


def test_transaction_is_translated():
    """Ensure we use beancount quoted payee syntax and two-space indent"""
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Restaurants    40 USD
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Restaurants        40 USD
      Assets:Cash
    """)


def test_currency_is_translated():
    """$40 -> 40 USD"""
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Restaurants    $40
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Restaurants        40 USD
      Assets:Cash
    """)


def test_balance_assertions_are_translated():
    input = from_triple_quoted_string("""
    2017-01-02 Blah blah
        Assets:Cash   = $40
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    * Transactions
    2017-01-02 balance Assets:Cash   40 USD
    """)


def test_balance_assertions_cannot_mix_with_other_postings_1():
    input = from_triple_quoted_string("""
    2017-01-02 Blah blah
        Assets:Cash   = $40
        Expenses:Cash
    """)
    with pytest.raises(BalanceAssertionTooComplicated):
        translate_file(input)


def test_balance_assertions_cannot_mix_with_other_postings_2():
    input = from_triple_quoted_string("""
    2017-01-02 Blah blah
        Expenses:Cash   $40
        Assets:Cash   = $40
    """)
    with pytest.raises(BalanceAssertionTooComplicated):
        translate_file(input)


def test_balance_assertions_cannot_mix_with_other_postings_3():
    """This is more of a bug than a feature"""
    input = from_triple_quoted_string("""
    2017-01-02 Blah blah
        Assets:Cash   $15 = $40
        Expenses:Cash   $-15
    """)
    with pytest.raises(BalanceAssertionTooComplicated):
        translate_file(input)


def test_allow_balance_assertions_with_zero():
    input = from_triple_quoted_string("""
    2017-01-02 Blah blah
        Assets:Cash   $0 = $40
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    * Transactions
    2017-01-02 balance Assets:Cash   40 USD
    """)


def test_comments_are_preserved_after_statements():
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction   ; Payee comment
        ; Transaction comment
        Expenses:Restaurants    40 USD   ; Posting comment
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"   ; Payee comment
      ; Transaction comment
      Expenses:Restaurants        40 USD   ; Posting comment
      Assets:Cash
    """)
