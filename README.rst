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
