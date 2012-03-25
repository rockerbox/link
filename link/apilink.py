"""
apilink contains all of the classes that you need to connect to a configured
api.  It wraps the python requests package, and provides some helpful functions
that make it easy to parse json and xml responses
"""
import requests
from requests.auth import HTTPBasicAuth
from functools import wraps
import json
from xml.etree import cElementTree as ET
from link import Linker, Wrapper


class ResponseWrapper(Wrapper):
    """
    Wrap an API response and make it easy to parse out
    json or XML
    """
    def __init__(self, response, wrap_name = None):
        self._json = None
        self._xml = None
        super(ResponseWrapper, self).__init__(wrap_name, response)

    @property
    def json(self):
        """
        json's the content and returns it as a dictionary
        """
        if not self._json:
            try:
                self._json = json.loads(self.content)
            except:
                raise ValueError("Response is not valid json %s " % self.content)
        return self._json

    @property
    def xml(self):
        """
        json's the content and returns it as a dictionary
        """
        if not self._xml:
            try:
                self._xml = ET.XML(self.content)
            except:
                raise ValueError("Response is not valid xml %s " % self.content)
        return self._xml

    def tostring(self):
        """
        If you have parsed json or xml it will
        return the manipulated object as a string.  Might not be a very helpful
        function
        """
        if self._json:
            return json.dumps(self._json)

        if self._xml:
            return ET.tostring(self._xml)


class RequestWrapper(Wrapper):
    """
    Wraps the requests class so that all you have to give is
    extra url parameters for it to work fine
    """
    requests = requests
    headers = {'Accept': '*/*',
                        'Accept-Encoding': 'identity, deflate, compress, gzip',
                        'User-Agent': 'python-requests/0.8.3'
                      }

    def __init__(self, wrap_name=None, base_url=None, user=None, password=None):
        self.base_url = base_url
        self.user = user
        self.password = password
        #we will use the requests package to be the one wrapped but we could use
        #our own
        self._auth = None 
        self._authed = False
        super(RequestWrapper, self).__init__(wrap_name, self.requests)
    
    @property
    def auth(self):
        """
        The Auth Property uses HTTPBasicAuth by defaust, but you can override
        this property if you want to use another type or auth.  The result
        is passed into requests.auth. 
        """
        if self._authed or self._auth is not None:
            return self._auth

        if self.user and self.password:
            self._auth = HTTPBasicAuth(self.user, self.password)
            self._authed = True

        return self._auth 

    def request(self, method='get', url_params = '' , data = '', use_auth=True):
        """
        Make a request.  This is taken care af by the request decorator
        """
        if isinstance(url_params, dict):
            #tricky, if its a dictonary turn it into a & delimited key=value
            url_params = '&'.join([ '%s=%s' % (key, value) for key,value
                                   in url_params.items()])

        full_url = self.base_url + url_params
        #turn the string method into a function name
        method = self.requests.__getattribute__(method)
    
        #if we are supposed to use auth then call it 
        auth = None
        if use_auth:
            auth = self.auth

        return ResponseWrapper(method(full_url, auth = auth,
                                        headers = self.headers, data = data))

    def get(self, url_params = '', use_auth=True):
        """
        Make a get call
        """
        return self.request('get', url_params = url_params, use_auth = use_auth)

    def put(self, url_params='', data='', use_auth=True):
        """
        Make a put call
        """
        return self.request('put', url_params = url_params, data = data, 
                            use_auth = use_auth)

    def post(self, url_params='', data='', use_auth=True):
        """
        Make a post call
        """
        return self.request('post', url_params = url_params, data = data,
                            use_auth=use_auth)

    def add_to_headers(self, key, value):
        self.headers[key] = value


class APILink(Linker):
    """
    The linked API handler which gives you access to all of your configured
    API's.  It will return an APIWrapper
    """
    def __init__(self, wrapper_object = RequestWrapper):
        super(APILink, self).__init__('apis', wrapper_object)
