#!/usr/local/bin/python
"""
This is a py.test script

Example usage on Unix:
bitly-api-python $ BITLY_ACCESS_TOKEN=<accesstoken> nosetests
or 'export' the two environment variables prior to running nosetests
"""
import os
import sys
sys.path.append('../')
import bitly_api

BITLY_ACCESS_TOKEN = "BITLY_ACCESS_TOKEN"


def get_connection():
    """Create a Connection base on username and access token credentials"""
    if BITLY_ACCESS_TOKEN not in os.environ:
        raise ValueError("Environment variable '{}' required".format(BITLY_ACCESS_TOKEN))
    access_token = os.getenv(BITLY_ACCESS_TOKEN)
    bitly = bitly_api.Connection(access_token=access_token)
    return bitly


def testApi():
    bitly = get_connection()
    data = bitly.shorten('http://google.com/')
    assert data is not None
    assert data['long_url'] == 'http://google.com/'
    assert data['hash'] is not None


def testExpand():
    bitly = get_connection()
    data = bitly.expand(hash='test1_random_fjslfjieljfklsjflkas')
    assert data is not None
    assert len(data) == 1
    assert data[0]['error'] == 'NOT_FOUND'


def testReferrer():
    bitly = get_connection()
    data = bitly.referrers(hash='a')
    assert data is not None
    assert len(data) > 1


def testProDomain():
    bitly = get_connection()
    test_data = {
        'cnn.com': False,
        'nyti.ms': True,
        'g.co': False,
        'j.mp': False,
        'pep.si': True,
        'http://pep.si': 'INVALID_BARE_DOMAIN',
    }
    for domain in test_data:
        try:
            result = bitly.pro_domain(domain)
            assert result == test_data[domain], domain
        except bitly_api.BitlyError as e:
            assert str(e) == test_data[domain]


def testUserInfo():
    bitly = get_connection()
    data = bitly.user_info()
    assert data is not None
    assert 'login' in data
