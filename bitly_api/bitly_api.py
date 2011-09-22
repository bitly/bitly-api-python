import bitly_http
import hashlib
try:
    import json
except ImportError:
    import simplejson as json
import sys
import time
import types
import urllib

class Error(Exception):
    pass

class BitlyError(Error):
    def __init__(self, code, message):
        Error.__init__(self,message)
        self.code = code


class Connection(object):
    """
    This is a python library for accessing the bit.ly api
    http://github.com/bitly/bitly-api-python
    
    Usage:
        import bitly_api
        c = bitly_api.Connection('bitlyapidemo','R_{{apikey}}')
        c.shorten('http://www.google.com/')
    """
    def __init__(self, login, api_key, secret=None, preferred_domain='bit.ly'):
        self.host = 'api.bit.ly'
        self.preferred_domain = preferred_domain # bit.ly or j.mp
        self.login = login
        self.api_key = api_key
        self.secret = secret
        (major, minor, micro, releaselevel, serial) = sys.version_info
        self.user_agent = "Python/%d.%d.%d bitly_api/%s" % (major, minor, micro, '?')
    
    def keyword(self, hash, keyword):
        """ assign a keyword to a hash """
        data = self._call(self.host, 'v3/keyword', {
                'login':self.login,
                'apiKey':self.api_key,
                'hash':hash,
                'keyword':keyword
            }, self.secret)
        return data['data']
    
    def shorten(self, uri, x_login=None, x_apiKey=None, preferred_domain=None):
        """ creates a bit.ly link for a given long url 
        @parameter uri: long url to shorten
        @parameter x_login: login of a user to shorten on behalf of
        @parameter x_apiKey: apiKey of a user to shorten on behalf of
        @parameter preferred_domain: bit.ly[default] or j.mp
        """
        preferred_domain = preferred_domain or self.preferred_domain
        params = {
            'login': self.login,
            'apiKey': self.api_key,
            'uri':uri.encode('UTF-8')
        }
        if preferred_domain:
            params['domain'] = preferred_domain
        if x_login:
            params.update({
                'x_login':x_login,
                'x_apiKey':x_apiKey})
        data = self._call(self.host, 'v3/shorten', params, self.secret)
        return data['data']
    
    def expand(self, hash=None, shortUrl=None):
        """ given a bit.ly url or hash, decode it and return the target url
        @parameter hash: one or more bit.ly hashes
        @parameter shortUrl: one or more bit.ly short urls
        """
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = {
            'login' : self.login,
            'apiKey' : self.api_key
        }
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl
            
        data = self._call(self.host, 'v3/expand', params, self.secret)
        return data['data']['expand']

    def clicks(self, hash=None, shortUrl=None):
        """ given a bit.ly url or hash, get statistics about the clicks on that link """
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = {
            'login' : self.login,
            'apiKey' : self.api_key
        }
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/clicks', params, self.secret)
        return data['data']['clicks']

    def referrers(self, hash=None, shortUrl=None):
        """ given a bit.ly url or hash, get statistics about the referrers of that link """
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = {
            'login' : self.login,
            'apiKey' : self.api_key
        }
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/referrers', params, self.secret)
        return data['data']['referrers']
    
    def clicks_by_day(self, hash=None, shortUrl=None):
        """ given a bit.ly url or hash, get a time series of clicks
        per day for the last 30 days in reverse chronological order
        (most recent to least recent) """
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = {
            'login' : self.login,
            'apiKey' : self.api_key
        }
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/clicks_by_day', params, self.secret)
        return data['data']['clicks_by_day']
    
    def clicks_by_minute(self, hash=None, shortUrl=None):
        """ given a bit.ly url or hash, get a time series of clicks
        per minute for the last 30 minutes in reverse chronological
        order (most recent to least recent)"""
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = {
            'login' : self.login,
            'apiKey' : self.api_key
        }
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/clicks_by_minute', params, self.secret)
        return data['data']['clicks_by_minute']

    def info(self, hash=None, shortUrl=None):
        """ return the page title for a given bit.ly link """
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = {
            'login' : self.login,
            'apiKey' : self.api_key
        }
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/info', params, self.secret)
        return data['data']['info']
    
    def lookup(self, url):
        """ query for a bit.ly link based on a long url """
        params = {
            'url' : url,
            'login' : self.login,
            'apiKey' : self.api_key
        }

        data = self._call(self.host, 'v3/lookup', params, self.secret)
        return data['data']['lookup']

    def pro_domain(self, domain, format='json'):
        """ is the domain assigned for bitly.pro? """
        end_point = 'v3/bitly_pro_domain'

        if not domain:
            raise BitlyError(500, 'MISSING_ARG_DOMAIN')

        protocol_prefix = ('http://', 'https://')
        if domain.lower().startswith(protocol_prefix):
            raise BitlyError(500, 'INVALID_BARE_DOMAIN')
        params = {
            'domain': domain,
            'login' : self.login,
            'apiKey' : self.api_key,
            'format': format,
        }
        data = self._call(self.host, end_point, params, self.secret)
        return data['data']['bitly_pro_domain']

    @classmethod
    def _generateSignature(self, params, secret):
        if not params or not secret:
            return ""
        hash_string = ""
        if not params.get('t'):
            # note, this uses a utc timestamp not a local timestamp
            params['t'] = str(int(time.mktime(time.gmtime())))
        
        keys = params.keys()
        keys.sort()
        for k in keys:
            if type(params[k]) in [types.ListType, types.TupleType]:
                for v in params[k]:
                    hash_string += v
            else:
                hash_string += params[k]
        hash_string += secret
        signature = hashlib.md5(hash_string).hexdigest()[:10]
        return signature
    
    def _call(self, host, method, params, secret=None, timeout=2500):
        # default to json
        params['format']=params.get('format','json')
        
        if secret:
            params['signature'] = self._generateSignature(params, secret)
        
        # force to utf8 to fix ascii codec errors
        encoded_params = []
        for k,v in params.items():
            if type(v) in [types.ListType, types.TupleType]:
                v = [e.encode('UTF8') for e in v]
            else:
                v = v.encode('UTF8')
            encoded_params.append((k,v))
        params = dict(encoded_params)
        
        request = "http://%(host)s/%(method)s?%(params)s" % {
            'host':host,
            'method':method,
            'params':urllib.urlencode(params, doseq=1)
            }
        try:
            http_response = bitly_http.get(request, timeout, user_agent = self.user_agent)
            if http_response['http_status_code'] != 200:
                raise BitlyError(500, http_response['result'])
            if not http_response['result'].startswith('{'):
                raise BitlyError(500, http_response['result'])
            data = json.loads(http_response['result'])
            if data.get('status_code', 500) != 200:
                raise BitlyError(data.get('status_code', 500), data.get('status_txt', 'UNKNOWN_ERROR'))
            return data
        except BitlyError:
            raise
        except:
            raise BitlyError(None, sys.exc_info()[1])

