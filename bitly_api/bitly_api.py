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
import warnings

class Error(Exception):
    pass

class BitlyError(Error):
    def __init__(self, code, message):
        Error.__init__(self,message)
        self.code = code

def _utf8(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    assert isinstance(s, str)
    return s

class Connection(object):
    """
    This is a python library for accessing the bitly api
    http://github.com/bitly/bitly-api-python
    
    Usage:
        import bitly_api
        c = bitly_api.Connection('bitlyapidemo','R_{{apikey}}')
        # or to use oauth2 endpoints
        c = bitly_api.Connection(access_token='...')
        c.shorten('http://www.google.com/')
    """
    
    def __init__(self, login=None, api_key=None, access_token=None, secret=None):
        self.host = 'api.bitly.com'
        self.login = login
        self.api_key = api_key
        self.access_token = access_token
        self.secret = secret
        (major, minor, micro, releaselevel, serial) = sys.version_info
        self.user_agent = "Python/%d.%d.%d bitly_api/%s" % (major, minor, micro, '?')
    
    def shorten(self, uri, x_login=None, x_apiKey=None, preferred_domain=None):
        """ creates a bitly link for a given long url 
        @parameter uri: long url to shorten
        @parameter x_login: login of a user to shorten on behalf of
        @parameter x_apiKey: apiKey of a user to shorten on behalf of
        @parameter preferred_domain: bit.ly[default], bitly.com, or j.mp
        """
        params = dict(uri=uri)
        if preferred_domain:
            params['domain'] = preferred_domain
        if x_login:
            params.update({
                'x_login':x_login,
                'x_apiKey':x_apiKey})
        data = self._call(self.host, 'v3/shorten', params, self.secret)
        return data['data']
    
    def expand(self, hash=None, shortUrl=None):
        """ given a bitly url or hash, decode it and return the target url
        @parameter hash: one or more bitly hashes
        @parameter shortUrl: one or more bitly short urls
        """
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = dict()
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl
            
        data = self._call(self.host, 'v3/expand', params, self.secret)
        return data['data']['expand']

    def clicks(self, hash=None, shortUrl=None):
        """ given a bitly url or hash, get statistics about the clicks on that link """
        warnings.warn("/v3/clicks is depricated in favor of /v3/link/clicks", DeprecationWarning)
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = dict()
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/clicks', params, self.secret)
        return data['data']['clicks']
    

    def referrers(self, hash=None, shortUrl=None):
        """ given a bitly url or hash, get statistics about the referrers of that link """
        warnings.warn("/v3/referrers is depricated in favor of /v3/link/referrers", DeprecationWarning)
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = dict()
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/referrers', params, self.secret)
        return data['data']['referrers']
    
    def clicks_by_day(self, hash=None, shortUrl=None):
        """ given a bitly url or hash, get a time series of clicks
        per day for the last 30 days in reverse chronological order
        (most recent to least recent) """
        warnings.warn("/v3/clicks_by_day is depricated in favor of /v3/link/clicks?unit=day", DeprecationWarning)
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = dict()
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/clicks_by_day', params, self.secret)
        return data['data']['clicks_by_day']
    
    def clicks_by_minute(self, hash=None, shortUrl=None):
        """ given a bitly url or hash, get a time series of clicks
        per minute for the last 30 minutes in reverse chronological
        order (most recent to least recent)"""
        warnings.warn("/v3/clicks_by_minute is depricated in favor of /v3/link/clicks?unit=minute", DeprecationWarning)
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = dict()
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/clicks_by_minute', params, self.secret)
        return data['data']['clicks_by_minute']

    def link_clicks(self, link, **kwargs):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/clicks", params, **kwargs)
        return data["link_clicks"]

    def link_referring_domains(self, link, **kwargs):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/referring_domains", params, **kwargs)
        return data["referring_domains"]

    def link_referrers(self, link, **kwargs):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/referrers", params, **kwargs)
        return data["referrers"]

    def link_countries(self, link, **kwargs):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/countries", params, **kwargs)
        return data["countries"]
    
    def user_popular_links(self, **kwargs):
        data = self._call_oauth2_metrics("v3/user/popular_links", dict(), **kwargs)
        return data["popular_links"]
        
    def user_shorten_counts(self, **kwargs):
        data = self._call_oauth2_metrics("v3/user/shorten_counts", dict(), **kwargs)
        return data["shorten_counts"]

    def user_tracking_domain_list(self):
        data = self._call_oauth2("v3/user/tracking_domain_list", dict())
        return data["tracking_domains"]
        
    def user_tracking_domain_clicks(self, domain, **kwargs):
        params = dict(domain=domain)
        data = self._call_oauth2_metrics("v3/user/tracking_domain_clicks", params, **kwargs)
        return data["tracking_domain_clicks"]
        
    def user_tracking_domain_shorten_counts(self, domain, **kwargs):
        params = dict(domain=domain)
        data = self._call_oauth2_metrics("v3/user/tracking_domain_shorten_counts", params, **kwargs)
        return data["tracking_domain_shorten_counts"]
        
    def user_link_history(self, created_before=None, created_after=None, archived=None, limit=None, offset=None):
        params = dict()
        if created_before is not None:
            assert isinstance(limit, int)
            params["created_before"] = created_before
        if created_after is not None:
            assert isinstance(limit, int)
            params["created_after"] = created_after
        if archived is not None:
            assert isinstance(archived, bool)
            params["archived"] = "true" if archived else "false"
        if limit is not None:
            assert isinstance(limit, int)
            params["limit"] = str(limit)
        if offset is not None:
            assert isinstance(offset, int)
            params["offset"] = str(offset)
        data = self._call_oauth2("v3/user/link_history", params)
        return data["link_history"]
    
    def info(self, hash=None, shortUrl=None):
        """ return the page title for a given bitly link """
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = dict()
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/info', params, self.secret)
        return data['data']['info']
    
    def lookup(self, url):
        """ query for a bitly link based on a long url """
        params = dict(url=url)

        data = self._call(self.host, 'v3/lookup', params, self.secret)
        return data['data']['lookup']

    def pro_domain(self, domain):
        """ is the domain assigned for bitly.pro? """
        end_point = 'v3/bitly_pro_domain'

        if not domain:
            raise BitlyError(500, 'MISSING_ARG_DOMAIN')

        protocol_prefix = ('http://', 'https://')
        if domain.lower().startswith(protocol_prefix):
            raise BitlyError(500, 'INVALID_BARE_DOMAIN')
        params = dict(domain=domain)
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

    def _call_oauth2_metrics(self, endpoint, params, unit=None, units=None, tz_offset=None, rollup=None, limit=None):
        if unit is not None:
            assert unit in ("minute", "hour", "day", "week", "mweek", "month")
            params["unit"] = unit
        if units is not None:
            assert isinstance(units, int), "Unit (%r) must be integer" % units
            params["units"] = units
        if tz_offset is not None:
            # tz_offset can either be a hour offset, or a timezone like North_America/New_York
            if isinstance(tz_offset, int):
                assert -12 <= tz_offset <= 12, "integer tz_offset must be between -12 and 12"
            else:
                assert isinstance(tz_offset, (str, unicode))
            params["tz_offset"] = tz_offset
        if rollup is not None:
            assert isinstance(rollup, bool)
            params["rollup"] = "true" if rollup else "false"
        if limit is not None:
            assert isinstance(limit, int)
            params["limit"] = str(limit)
        
        return self._call_oauth2(endpoint, params)
        
    def _call_oauth2(self, endpoint, params):
        assert self.access_token, "This %s endpoint requires OAuth" % endpoint
        return self._call(self.host, endpoint, params)["data"]
    
    def _call(self, host, method, params, secret=None, timeout=5000):
        params['format'] = params.get('format', 'json') # default to json

        if self.access_token:
            scheme = 'https'
            params['access_token'] = self.access_token
        else:
            scheme = 'http'
            params['login'] = self.login
            params['apiKey'] = self.api_key
            
        
        if secret:
            params['signature'] = self._generateSignature(params, secret)
        
        # force to utf8 to fix ascii codec errors
        encoded_params = []
        for k,v in params.items():
            if isinstance(v, (list, tuple)):
                v = [_utf8(e) for e in v]
            else:
                v = _utf8(v)
            encoded_params.append((k,v))
        params = dict(encoded_params)
        
        request = "%(scheme)s://%(host)s/%(method)s?%(params)s" % {
            'scheme': scheme,
            'host': host,
            'method': method,
            'params': urllib.urlencode(params, doseq=1)
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
        except Exception:
            raise BitlyError(None, sys.exc_info()[1])

