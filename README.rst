=====================
 ledger-to-beancount
=====================

Another ledger-to-beancount converter.

`plaintextaccounting
<http://plaintextaccounting.org/#data-importconversion>`_ contains a
link to `a Github gist called ledger2beancount.py
<https://gist.github.com/travisdahlke/71152286b0a8826249fe>`_. It's
not bad for what it does, but what it does is kind of incomplete. It
works by asking ledger for transactions, and then formats the
transactions. This means it doesn't include anything that isn't a
transaction, namely a comment or a balance assertion. In my ledger
use, these are both quite important, and I don't want to lose them or
have to copy them over by hand.

To address these concerns, we take a very different approach. Rather
than introspect on parsed ledger data, we examine a "raw" file and do
a crude syntactic translation from Ledger syntax to Beancount
syntax. This means we have to do some extra work to parse everything,
as well as handling aliases ourselves, but gives us access to
everything in the original Ledger file.

==============
 Installation
==============

::

  $ pip install https://github.com/glasserc/ledger-to-beancount.git

Run with::

  $ ledger-to-beancount <ledger file>

=======
 Tests
=======

Run with ``py.test``.

==========
 Features
==========

Given a .ledger file like this::

  2010-02-04 Purchasing new shoes
      Expenses:Clothing       $100
      Liabilities:Credit Card

  2010-02-05 Buying dinner at a Thai place
      Expenses:Restaurant
      Liabilities:Credit Card  $40
      Assets:Cash             $10   ; for the tip

  2010/2/6 Investing
      Assets:Investment     10 DJIA @ $13.01
      Assets:Investment

  2010-02-08 Reaping the gains
      Assets:Investment    -10 DJIA @ $14.01
      Assets:Investment

  2010-02-10 Balance assertion
      Assets:Investment   = $1000

The converter outputs::

  * Accounts
  2010-01-01 open Assets:Cash
  2010-01-01 open Assets:Investment
  2010-01-01 open Expenses:Clothing
  2010-01-01 open Expenses:Restaurant
  2010-01-01 open Liabilities:CreditCard
  * Transactions
  2010-02-04 * "Purchasing new shoes"
    Expenses:Clothing        100 USD
    Liabilities:CreditCard

  2010-02-05 * "Buying dinner at a Thai place"
    Expenses:Restaurant
    Liabilities:CreditCard      40 USD
    Assets:Cash        10 USD   ; for the tip

  2010-02-06 * "Investing"
    Assets:Investment        10 DJIA {13.01 USD}
    Assets:Investment

  2010-02-08 * "Reaping the gains"
    Assets:Investment        -10 DJIA @ 14.01 USD
    Assets:Investment

  2010-02-10 balance Assets:Investment   1000 USD

In other words:

- Dates are converted automatically to ISO8601 format.

- Currency is automatically converted.

- Transactions are converted to beancount format, i.e. with payees
  quoted (and escaped if necessary).

- Comments are preserved, even in tricky cases like at the end of a posting.

- Spacing is made uniform. (Two spaces for postings, eight spaces between an account and its amount, and three spaces after the account in a balance assertion.)

  - FIXME: It would be really neat to align monetary amounts in postings!

- Balance assertions are converted to beancount format.

- Purchases, but not sales, of all assets are converted to cost bases.

  - FIXME: This may not be correct if you do a lot of foreign currency exchange.

  - This may cause ``bean-check`` to complain on sales, since the cost
    bases are missing. Unfortunately, we have no way to generate this
    information. Consider the errors to be a helpful way to locate transactions :)
