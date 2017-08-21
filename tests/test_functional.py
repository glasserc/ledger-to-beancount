from ledger_to_beancount import translate_file


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
