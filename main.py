#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template

from google.appengine.api import memcache

from django.utils import simplejson

import extractlinks
from extractlinks import LinkExtractor 
import feedparser
import re
import urlparse

class MainHandler(webapp.RequestHandler):
  
  def render_json(self, obj):
    self.response.headers["Content-Type"] = 'text/javascript'
    if self.request.get("callback"):
      self.response.out.write(self.request.get("callback") + "(" + simplejson.dumps(obj) + ")")
    else:
      self.response.out.write(simplejson.dumps(obj))
    
  def get(self):
    # We need to clean up the url first and remove any fragment
    site_url = urlparse.urldefrag(self.request.get("url"))[0]
    force = self.request.get("force")
    feeds = [] # default value
    if site_url:
      feeds = memcache.get(site_url)
      if feeds is not None and not force:
        # good
        logging.debug("Memcache hit.")
        self.render_json(feeds)
      else:
        logging.debug("Memcache miss.")
        try:
          result = urlfetch.fetch(url=site_url, deadline=10)
          parser = LinkExtractor()
          parser.set_base_url(site_url)
          parser.feed(result.content)
          if parser.links:
            feeds = parser.links
          else:
            feeds = []
            
          if not feeds:
              # Let's check if by any chance this is actually not a feed?
              data = feedparser.parse(result.content)
              mimeType = "application/atom+xml"
              href = site_url
              if re.match("atom", data.version):
                  mimeType = "application/atom+xml"
              feeds = [{'title': data.feed.title, 'rel': 'self', 'type': mimeType, 'href': href}]
              
        except:
          feeds = []
        
        if not memcache.set(site_url, feeds, 86400):
          logging.error("Memcache set failed.")
        else: 
          logging.debug("Memcache set.")
        self.render_json(feeds)
        
          
    else:
      self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'templates', "index.html"), {}))
      
def main():
  application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
