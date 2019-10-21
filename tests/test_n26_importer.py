import datetime
from textwrap import dedent

from beancount.core.number import Decimal
import pytest

from beancount_n26 import _header_for, N26Importer

IBAN_NUMBER = 'DE99 9999 9999 9999 9999 99'.replace(' ', '')


def _format(string, **kwargs):
    kwargs.update(
        {'iban_number': IBAN_NUMBER, 'header': ','.join(_header_for('en'))}
    )

    return dedent(string).format(**kwargs).lstrip().encode('utf-8')


@pytest.fixture
def importer():
    return N26Importer(IBAN_NUMBER, 'Assets:N26', 'en')


@pytest.fixture
def filename(tmp_path):
    return tmp_path / f'{IBAN_NUMBER}.csv'


def test_en_identify_correct(importer, filename):
    with open(filename, 'wb') as fd:
        fd.write(
            _format(
                '''
                {header}
                "2019-10-10","MAX MUSTERMANN","{iban_number}","Outgoing Transfer","Muster GmbH","Miscellaneous","-12.34","","",""
                '''  # NOQA
            )
        )

    with open(filename) as fd:
        assert importer.identify(fd)


def test_en_extract_no_transactions(importer, filename):
    with open(filename, 'wb') as fd:
        fd.write(
            _format(
                '''
                {header}
                '''
            )
        )

    with open(filename) as fd:
        transactions = importer.extract(fd)

    assert len(transactions) == 0


def test_en_extract_single_transaction(importer, filename):
    with open(filename, 'wb') as fd:
        fd.write(
            _format(
                '''
                {header}
                "2019-10-10","MAX MUSTERMANN","{iban_number}","Outgoing Transfer","Muster GmbH","Miscellaneous","-12.34","","",""
                '''  # NOQA
            )
        )

    with open(filename) as fd:
        transactions = importer.extract(fd)

    assert len(transactions) == 1
    assert transactions[0].date == datetime.date(2019, 10, 10)
    assert transactions[0].payee == 'MAX MUSTERMANN'
    assert transactions[0].narration == 'Muster GmbH'

    assert len(transactions[0].postings) == 1
    assert transactions[0].postings[0].account == 'Assets:N26'
    assert transactions[0].postings[0].units.currency == 'EUR'
    assert transactions[0].postings[0].units.number == Decimal('-12.34')