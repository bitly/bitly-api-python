import hashlib
import json
import sys
import time
import types
import warnings

try:
    from urllib.request import build_opener, HTTPRedirectHandler
    from urllib.parse import urlencode
    from urllib.error import URLError, HTTPError
    string_types = str,
    integer_types = int,
    numeric_types = (int, float)
    text_type = str
    binary_type = bytes
except ImportError as e:
    from urllib2 import build_opener, HTTPRedirectHandler, URLError, HTTPError
    from urllib import urlencode
    string_types = basestring,
    integer_types = (int, long)
    numeric_types = (int, long, float)
    text_type = unicode
    binary_type = str


class DontRedirect(HTTPRedirectHandler):
    def redirect_response(self, req, fp, code, msg, headers, newurl):
        if code in (301, 302, 303, 307):
            raise HTTPError(req.get_full_url(), code, msg, headers, fp)


class Error(Exception):
    pass


class BitlyError(Error):
    def __init__(self, code, message):
        Error.__init__(self, message)
        self.code = code


def _utf8(s):
    if isinstance(s, text_type):
        s = s.encode('utf-8')
    assert isinstance(s, binary_type)
    return s


def _utf8_params(params):
    """encode a dictionary of URL parameters (including iterables) as utf-8"""
    assert isinstance(params, dict)
    encoded_params = []
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, numeric_types):
            v = str(v)
        if isinstance(v, (list, tuple)):
            v = [_utf8(x) for x in v]
        else:
            v = _utf8(v)
        encoded_params.append((k, v))
    return dict(encoded_params)


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

    def __init__(self, login=None, api_key=None, access_token=None,
                 secret=None):
        self.host = 'api.bit.ly'
        self.ssl_host = 'api-ssl.bit.ly'
        self.login = login
        self.api_key = api_key
        self.access_token = access_token
        self.secret = secret
        (major, minor, micro, releaselevel, serial) = sys.version_info
        parts = (major, minor, micro, '?')
        self.user_agent = "Python/%d.%d.%d bitly_api/%s" % parts

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
                'x_login': x_login,
                'x_apiKey': x_apiKey})
        data = self._call(self.host, 'v3/shorten', params, self.secret)
        return data['data']

    def expand(self, hash=None, shortUrl=None, link=None):
        """ given a bitly url or hash, decode it and return the target url
        @parameter hash: one or more bitly hashes
        @parameter shortUrl: one or more bitly short urls
        @parameter link: one or more bitly short urls (preferred vocabulary)
        """
        if link and not shortUrl:
            shortUrl = link

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
        """
        given a bitly url or hash, get statistics about the clicks on that link
        """
        warnings.warn("/v3/clicks is depricated in favor of /v3/link/clicks",
                      DeprecationWarning)
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
        """
        given a bitly url or hash, get statistics about the referrers of that
        link
        """
        warnings.warn("/v3/referrers is depricated in favor of "
                      "/v3/link/referrers", DeprecationWarning)
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
        warnings.warn("/v3/clicks_by_day is depricated in favor of "
                      "/v3/link/clicks?unit=day", DeprecationWarning)
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
        warnings.warn("/v3/clicks_by_minute is depricated in favor of "
                      "/v3/link/clicks?unit=minute", DeprecationWarning)
        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = dict()
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/clicks_by_minute', params,
                          self.secret)
        return data['data']['clicks_by_minute']

    def link_clicks(self, link, **kwargs):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/clicks", params, **kwargs)
        return data["link_clicks"]

    def link_encoders(self, link, **kwargs):
        """return the bitly encoders who have saved this link"""
        params = dict(link=link)
        data = self._call(self.host, 'v3/link/encoders', params, **kwargs)
        return data['data']

    def link_encoders_count(self, link, **kwargs):
        """return the count of bitly encoders who have saved this link"""
        params = dict(link=link)
        data = self._call(self.host, 'v3/link/encoders_count', params,
                          **kwargs)
        return data['data']

    def link_referring_domains(self, link, **kwargs):
        """
        returns the domains that are referring traffic to a single bitly link
        """
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/referring_domains", params,
                                         **kwargs)
        return data["referring_domains"]

    def link_referrers_by_domain(self, link, **kwargs):
        """
        returns the pages that are referring traffic to a single bitly link,
        grouped by domain
        """
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/referrers_by_domain", params,
                                         **kwargs)
        return data["referrers"]

    def link_referrers(self, link, **kwargs):
        """
        returns the pages are are referring traffic to a single bitly link
        """
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/referrers", params, **kwargs)
        return data["referrers"]

    def link_shares(self, link, **kwargs):
        """return number of shares of a bitly link"""
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/shares", params, **kwargs)
        return data

    def link_countries(self, link, **kwargs):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/countries", params, **kwargs)
        return data["countries"]

    def user_clicks(self, **kwargs):
        """aggregate number of clicks on all of this user's bitly links"""
        data = self._call_oauth2_metrics('v3/user/clicks', dict(), **kwargs)
        return data

    def user_countries(self, **kwargs):
        """
        aggregate metrics about countries from which people are clicking on all
        of a user's bitly links
        """
        data = self._call_oauth2_metrics('v3/user/countries', dict(), **kwargs)
        return data["countries"]

    def user_popular_links(self, **kwargs):
        data = self._call_oauth2_metrics("v3/user/popular_links", dict(),
                                         **kwargs)
        return data["popular_links"]

    def user_referrers(self, **kwargs):
        """
        aggregate metrics about the referrers for all of the authed user's
        bitly links
        """
        data = self._call_oauth2_metrics("v3/user/referrers", dict(), **kwargs)
        return data["referrers"]

    def user_referring_domains(self, **kwargs):
        """
        aggregate metrics about the domains referring traffic to all of the
        authed user's bitly links
        """
        data = self._call_oauth2_metrics("v3/user/referring_domains", dict(),
                                         **kwargs)
        return data["referring_domains"]

    def user_share_counts(self, **kwargs):
        """number of shares by authed user in given time period"""
        data = self._call_oauth2_metrics("v3/user/share_counts", dict(),
                                         **kwargs)
        return data["share_counts"]

    def user_share_counts_by_share_type(self, **kwargs):
        """
        number of shares by authed user broken down by type (facebook, twitter,
        email) in a give time period
        """
        data = self._call_oauth2_metrics("v3/user/share_counts_by_share_type",
                                         dict(), **kwargs)
        return data["share_counts_by_share_type"]

    def user_shorten_counts(self, **kwargs):
        data = self._call_oauth2_metrics("v3/user/shorten_counts", dict(),
                                         **kwargs)
        return data["user_shorten_counts"]

    def user_tracking_domain_list(self):
        data = self._call_oauth2("v3/user/tracking_domain_list", dict())
        return data["tracking_domains"]

    def user_tracking_domain_clicks(self, domain, **kwargs):
        params = dict(domain=domain)
        data = self._call_oauth2_metrics("v3/user/tracking_domain_clicks",
                                         params, **kwargs)
        return data["tracking_domain_clicks"]

    def user_tracking_domain_shorten_counts(self, domain, **kwargs):
        params = dict(domain=domain)
        data = self._call_oauth2_metrics(
            "v3/user/tracking_domain_shorten_counts", params, **kwargs)
        return data["tracking_domain_shorten_counts"]

    def user_info(self, **kwargs):
        """return or update info about a user"""
        data = self._call_oauth2("v3/user/info", kwargs)
        return data

    def user_link_history(self, created_before=None, created_after=None,
                          archived=None, limit=None, offset=None,
                          private=None):
        params = dict()
        if created_before is not None:
            assert isinstance(limit, integer_types)
            params["created_before"] = created_before
        if created_after is not None:
            assert isinstance(limit, integer_types)
            params["created_after"] = created_after
        if archived is not None:
            assert isinstance(archived, string_types)
            archived = archived.lower()
            assert archived is "on" or "off" or "both"
            params["archived"] = archived
        if private is not None:
            assert isinstance(private, string_types)
            private = private.lower()
            assert private is "on" or "off" or "both"
            params["private"] = private
        if limit is not None:
            assert isinstance(limit, integer_types)
            params["limit"] = str(limit)
        if offset is not None:
            assert isinstance(offset, integer_types)
            params["offset"] = str(offset)
        data = self._call_oauth2("v3/user/link_history", params)
        return data["link_history"]

    def user_network_history(self, offset=None, expand_client_id=False,
                             limit=None, expand_user=False):
        params = dict()
        if expand_client_id is True:
            params["expand_client_id"] = "true"
        if expand_user is True:
            params["expand_user"] = "true"
        if offset is not None:
            assert isinstance(offset, integer_types)
            params["offset"] = str(offset)
        if limit is not None:
            assert isinstance(limit, integer_types)
            params["limit"] = str(limit)
        data = self._call_oauth2("v3/user/network_history", params)
        return data

    def info(self, hash=None, shortUrl=None, link=None):
        """ return the page title for a given bitly link """
        if link and not shortUrl:
            shortUrl = link

        if not hash and not shortUrl:
            raise BitlyError(500, 'MISSING_ARG_SHORTURL')
        params = dict()
        if hash:
            params['hash'] = hash
        if shortUrl:
            params['shortUrl'] = shortUrl

        data = self._call(self.host, 'v3/info', params, self.secret)
        return data['data']['info']

    def link_lookup(self, url):
        """query for a bitly link based on a long url (or list of long urls)"""
        params = dict(url=url)
        data = self._call(self.host, 'v3/link/lookup', params, self.secret)
        return data['data']['link_lookup']

    def lookup(self, url):
        """ query for a bitly link based on a long url """
        warnings.warn("/v3/lookup is depricated in favor of /v3/link/lookup",
                      DeprecationWarning)

        params = dict(url=url)

        data = self._call(self.host, 'v3/lookup', params, self.secret)
        return data['data']['lookup']

    def user_link_edit(self, link, edit, title=None, note=None, private=None,
                       user_ts=None, archived=None):
        """edit a link in a user's history"""
        params = dict()

        if not link:
            raise BitlyError(500, 'MISSING_ARG_LINK')

        if not edit:
            raise BitlyError(500, 'MISSING_ARG_EDIT')

        params['link'] = link
        params['edit'] = edit
        if title is not None:
            params['title'] = str(title)
        if note is not None:
            params['note'] = str(note)
        if private is not None:
            params['private'] = bool(private)
        if user_ts is not None:
            params['user_ts'] = user_ts
        if archived is not None:
            params['archived'] = archived

        data = self._call_oauth2("v3/user/link_edit", params)
        return data['link_edit']

    def user_link_lookup(self, url):
        """
        query for whether a user has shortened a particular long URL. don't
        confuse with v3/link/lookup.
        """
        params = dict(url=url)
        data = self._call(self.host, 'v3/user/link_lookup', params,
                          self.secret)
        return data['data']['link_lookup']

    def user_link_save(self, longUrl=None, long_url=None, title=None,
                       note=None, private=None, user_ts=None):
        """save a link into the user's history"""
        params = dict()
        if not longUrl and not long_url:
            raise BitlyError('500', 'MISSING_ARG_LONG_URL')
        params['longUrl'] = longUrl or long_url
        if title is not None:
            params['title'] = str(title)
        if note is not None:
            params['note'] = str(note)
        if private is not None:
            params['private'] = bool(private)
        if user_ts is not None:
            params['user_ts'] = user_ts

        data = self._call_oauth2("v3/user/link_save", params)
        return data['link_save']

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

    def bundle_archive(self, bundle_link):
        """archive a bundle for the authenticated user"""
        params = dict(bundle_link=bundle_link)
        data = self._call_oauth2_metrics("v3/bundle/archive", params)
        return data

    def bundle_bundles_by_user(self, user=None, expand_user=False):
        """list bundles by user (defaults to authed user)"""
        params = dict()
        if user is not None:
            params["user"] = user
        if expand_user is True:
            params["expand_user"] = "true"
        data = self._call_oauth2_metrics("v3/bundle/bundles_by_user", params)
        return data

    def bundle_clone(self, bundle_link):  # TODO: 500s
        """clone a bundle for the authenticated user"""
        params = dict(bundle_link=bundle_link)
        data = self._call_oauth2_metrics("v3/bundle/clone", params)
        return data

    def bundle_collaborator_add(self, bundle_link, collaborator=None):
        """add a collaborator a bundle"""
        params = dict(bundle_link=bundle_link)
        if collaborator is not None:
            params["collaborator"] = collaborator
        data = self._call_oauth2_metrics("v3/bundle/collaborator_add", params)
        return data

    def bundle_collaborator_remove(self, bundle_link, collaborator):
        """remove a collaborator from a bundle"""
        params = dict(bundle_link=bundle_link)
        params["collaborator"] = collaborator
        data = self._call_oauth2_metrics("v3/bundle/collaborator_remove",
                                         params)
        return data

    def bundle_contents(self, bundle_link, expand_user=False):
        """list the contents of a bundle"""
        params = dict(bundle_link=bundle_link)
        if expand_user:
            params["expand_user"] = "true"
        data = self._call_oauth2_metrics("v3/bundle/contents", params)
        return data

    def bundle_create(self, private=False, title=None, description=None):
        """create a bundle"""
        params = dict()
        if private:
            params["private"] = "true"
        if title is not None:
            assert isinstance(title, string_types)
            params["title"] = title
        if description is not None:
            assert isinstance(description, string_types)
            params["description"] = description
        data = self._call_oauth2_metrics("v3/bundle/create", params)
        return data

    def bundle_edit(self, bundle_link, edit=None, title=None, description=None,
                    private=None, preview=None, og_image=None):
        """edit a bundle for the authenticated user"""
        params = dict(bundle_link=bundle_link)
        if edit:
            assert isinstance(edit, string_types)
            params["edit"] = edit
        if title:
            assert isinstance(title, string_types)
            params["title"] = title
        if description:
            assert isinstance(description, string_types)
            params["description"] = description
        if private is not None:
            if private:
                params["private"] = "true"
            else:
                params["private"] = "false"
        if preview is not None:
            if preview:
                params["preview"] = "true"
            else:
                params["preview"] = "false"
        if og_image:
            assert isinstance(og_image, string_types)
            params["og_image"] = og_image
        data = self._call_oauth2_metrics("v3/bundle/edit", params)
        return data

    def bundle_link_add(self, bundle_link, link, title=None):
        """add a link to a bundle"""
        params = dict(bundle_link=bundle_link, link=link)
        if title:
            assert isinstance(title, string_types)
            params["title"] = title
        data = self._call_oauth2_metrics("v3/bundle/link_add", params)
        return data

    def bundle_link_comment_add(self, bundle_link, link, comment):
        """add a comment to a link in a bundle"""
        params = dict(bundle_link=bundle_link, link=link, comment=comment)
        data = self._call_oauth2_metrics("v3/bundle/link_comment_add", params)
        return data

    def bundle_link_comment_edit(self, bundle_link, link, comment_id, comment):
        """edit a comment on a link in a bundle"""
        params = dict(bundle_link=bundle_link, link=link,
                      comment_id=comment_id, comment=comment)
        data = self._call_oauth2_metrics("v3/bundle/link_comment_edit", params)
        return data

    def bundle_link_comment_remove(self, bundle_link, link, comment_id):
        """ remove a comment on a link in a bundle"""
        params = dict(bundle_link=bundle_link, link=link,
                      comment_id=comment_id)
        data = self._call_oauth2_metrics("v3/bundle/link_comment_remove",
                                         params)
        return data

    def bundle_link_edit(self, bundle_link, link, edit, title=None,
                         preview=None):
        """ edit the title for a link """
        params = dict(bundle_link=bundle_link, link=link)
        if edit == "title":
            params["edit"] = edit
            assert isinstance(title, string_types)
            params["title"] = title
        elif edit == "preview":
            params["edit"] = edit
            assert isinstance(preview, bool)
            if preview:
                params["preview"] = "true"
            else:
                params["preview"] = "false"
        else:
            raise BitlyError(500,
                             "PARAM EDIT MUST HAVE VALUE TITLE OR PREVIEW")
        data = self._call_oauth2_metrics("v3/bundle/link_edit", params)
        return data

    def bundle_link_remove(self, bundle_link, link):
        """ remove a link from a bundle """
        params = dict(bundle_link=bundle_link, link=link)
        data = self._call_oauth2_metrics("v3/bundle/link_remove", params)
        return data

    def bundle_link_reorder(self, bundle_link, link, display_order):
        """ reorder the links in a bundle"""
        params = dict(bundle_link=bundle_link, link=link,
                      display_order=display_order)
        data = self._call_oauth2_metrics("v3/bundle/link_reorder", params)
        return data

    def bundle_pending_collaborator_remove(self, bundle_link, collaborator):
        """remove a pending collaborator from a bundle"""
        params = dict(bundle_link=bundle_link)
        params["collaborator"] = collaborator
        data = self._call_oauth2_metrics(
            "v3/bundle/pending_collaborator_remove", params)
        return data

    def bundle_view_count(self, bundle_link):
        """ get the number of views on a bundle """
        params = dict(bundle_link=bundle_link)
        data = self._call_oauth2_metrics("v3/bundle/view_count", params)
        return data

    def user_bundle_history(self):
        """ return the bundles that this user has access to """
        data = self._call_oauth2_metrics("v3/user/bundle_history", dict())
        return data

    def highvalue(self, limit=10, lang='en'):
        params = dict(lang=lang)
        data = self._call_oauth2_metrics("v3/highvalue", params, limit=limit)
        return data

    def realtime_bursting_phrases(self):
        data = self._call_oauth2_metrics("v3/realtime/bursting_phrases",
                                         dict())
        return data["phrases"]

    def realtime_hot_phrases(self):
        data = self._call_oauth2_metrics("v3/realtime/hot_phrases", dict())
        return data["phrases"]

    def realtime_clickrate(self, phrase):
        params = dict(phrase=phrase)
        data = self._call_oauth2_metrics("v3/realtime/clickrate", params)
        return data["rate"]

    def link_info(self, link):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/info", params)
        return data

    def link_content(self, link, content_type="html"):
        params = dict(link=link, content_type=content_type)
        data = self._call_oauth2_metrics("v3/link/content", params)
        return data["content"]

    def link_category(self, link):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/category", params)
        return data["categories"]

    def link_social(self, link):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/social", params)
        return data["social_scores"]

    def link_location(self, link):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/location", params)
        return data["locations"]

    def link_language(self, link):
        params = dict(link=link)
        data = self._call_oauth2_metrics("v3/link/language", params)
        return data["languages"]

    def search(self, query, offset=None, cities=None, domain=None, fields=None,
               limit=10, lang='en'):
        params = dict(query=query, lang=lang)
        if offset:
            assert isinstance(offset, integer_types)
            params["offset"] = str(offset)
        if cities:  # TODO: check format
            assert isinstance(cities, string_types)
            params["cities"] = cities
        if domain:
            assert isinstance(domain, string_types)
            params["domain"] = domain
        if fields:
            assert isinstance(fields, string_types)
            params["fields"] = fields
        data = self._call_oauth2_metrics("v3/search", params, limit=limit)
        return data['results']

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

    def _call_oauth2_metrics(self, endpoint, params, unit=None, units=None,
                             tz_offset=None, rollup=None, limit=None,
                             unit_reference_ts=None):
        if unit is not None:
            assert unit in ("minute", "hour", "day", "week", "mweek", "month")
            params["unit"] = unit
        if units is not None:
            assert isinstance(units, integer_types), \
                "Unit (%r) must be integer" % units
            params["units"] = units
        if tz_offset is not None:
            # tz_offset can either be a hour offset, or a timezone like
            # North_America/New_York
            if isinstance(tz_offset, integer_types):
                msg = "integer tz_offset must be between -12 and 12"
                assert -12 <= tz_offset <= 12, msg
            else:
                assert isinstance(tz_offset, string_types)
            params["tz_offset"] = tz_offset
        if rollup is not None:
            assert isinstance(rollup, bool)
            params["rollup"] = "true" if rollup else "false"
        if limit is not None:
            assert isinstance(limit, integer_types)
            params["limit"] = limit
        if unit_reference_ts is not None:
            assert (unit_reference_ts == 'now' or
                    isinstance(unit_reference_ts, integer_types))
            params["unit_reference_ts"] = unit_reference_ts

        return self._call_oauth2(endpoint, params)

    def _call_oauth2(self, endpoint, params):
        assert self.access_token, "This %s endpoint requires OAuth" % endpoint
        return self._call(self.ssl_host, endpoint, params)["data"]

    def _call(self, host, method, params, secret=None, timeout=5000):
        params['format'] = params.get('format', 'json')  # default to json

        if self.access_token:
            scheme = 'https'
            params['access_token'] = self.access_token
            host = self.ssl_host
        else:
            scheme = 'http'
            params['login'] = self.login
            params['apiKey'] = self.api_key

        if secret:
            params['signature'] = self._generateSignature(params, secret)

        # force to utf8 to fix ascii codec errors
        params = _utf8_params(params)

        request = "%(scheme)s://%(host)s/%(method)s?%(params)s" % {
            'scheme': scheme,
            'host': host,
            'method': method,
            'params': urlencode(params, doseq=1)
            }

        try:
            opener = build_opener(DontRedirect())
            opener.addheaders = [('User-agent', self.user_agent + ' urllib')]
            response = opener.open(request)
            code = response.code
            result = response.read().decode('utf-8')
            if code != 200:
                raise BitlyError(500, result)
            if not result.startswith('{'):
                raise BitlyError(500, result)
            data = json.loads(result)
            if data.get('status_code', 500) != 200:
                raise BitlyError(data.get('status_code', 500),
                                 data.get('status_txt', 'UNKNOWN_ERROR'))
            return data
        except URLError as e:
            raise BitlyError(500, str(e))
        except HTTPError as e:
            raise BitlyError(e.code, e.read())
        except BitlyError:
            raise
        except Exception:
            raise BitlyError(None, sys.exc_info()[1])
