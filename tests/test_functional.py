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


def test_last_transaction_is_handled():
    """Ensure that if EOF happens during a transaction, we handle it"""
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Restaurants    40 USD
        Assets:Cash""")
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Restaurants        40 USD
      Assets:Cash""")  # There won't be an extra blank line


def test_account_name_is_translated():
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Eating Out    40 USD
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:EatingOut
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:EatingOut        40 USD
      Assets:Cash
    """)


def test_lowercase_account_name_is_translated():
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:eating out    40 USD
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Xeatingout
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Xeatingout        40 USD
      Assets:Cash
    """)


def test_invalid_account_name_is_translated():
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Eat&Out    40 USD
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:EatOut
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:EatOut        40 USD
      Assets:Cash
    """)


def test_payee_quotes_are_translated():
    input = from_triple_quoted_string("""
    2017-01-02 Eating at my "favorite" restaurant
        Expenses:Restaurants    40 USD
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "Eating at my \\"favorite\\" restaurant"
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


def test_negative_currency_is_translated():
    """$-40 -> -40 USD, as is -$40"""
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Restaurants    $-40
        Assets:Cash

    2017-01-02 Another ordinary transaction
        Expenses:Restaurants    -$40
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Restaurants        -40 USD
      Assets:Cash

    2017-01-02 * "Another ordinary transaction"
      Expenses:Restaurants        -40 USD
      Assets:Cash
    """)


def test_fractional_currency_is_translated():
    """$40.12 -> 40.12 USD"""
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Restaurants    $40.12
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Restaurants        40.12 USD
      Assets:Cash
    """)


def test_incomplete_decimals_are_translated():
    """$.12 -> 0.12 USD"""
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Restaurants    $.12
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Restaurants        0.12 USD
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


def test_balance_assertions_can_mix_with_comments():
    input = from_triple_quoted_string("""
    2017-01-02 Blah blah
        ; There are lots of important reasons why this is the balance
        ; at this particular moment in time. For starters, consider
        ; the global economic situation: a strong dollar combined with
        ; general instability
        Assets:Cash   = $40
        ; which doesn't even begin to enter the local, microeconomic factors
        ; such as my personal preference for a certain amount of cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    * Transactions
    2017-01-02 balance Assets:Cash   40 USD
      ; There are lots of important reasons why this is the balance
      ; at this particular moment in time. For starters, consider
      ; the global economic situation: a strong dollar combined with
      ; general instability
      ; which doesn't even begin to enter the local, microeconomic factors
      ; such as my personal preference for a certain amount of cash
    """)


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


def test_transform_price_to_cost_basis_buying():
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Restaurants    40 PDX  @ $1.10
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Restaurants        40 PDX {1.10 USD}
      Assets:Cash
    """)


def test_dont_transform_price_to_cost_basis_selling():
    input = from_triple_quoted_string("""
    2017-01-02 An ordinary transaction
        Expenses:Restaurants    -40 PDX  @ $1.10
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2017-01-02 * "An ordinary transaction"
      Expenses:Restaurants        -40 PDX @ 1.10 USD
      Assets:Cash
    """)


def test_translate_dates():
    input = from_triple_quoted_string("""
    2/6/2010 An ordinary transaction
        Expenses:Restaurants    $40
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2010-02-06 * "An ordinary transaction"
      Expenses:Restaurants        40 USD
      Assets:Cash
    """)

def test_translate_dates():
    input = from_triple_quoted_string("""
    2/6/2010 An ordinary transaction
        Expenses:Restaurants    $40
        Assets:Cash
    """)
    output = translate_file(input)
    assert output == from_triple_quoted_string("""
    * Accounts
    2010-01-01 open Assets:Cash
    2010-01-01 open Expenses:Restaurants
    * Transactions
    2010-02-06 * "An ordinary transaction"
      Expenses:Restaurants        40 USD
      Assets:Cash
    """)
