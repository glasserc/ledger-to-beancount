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