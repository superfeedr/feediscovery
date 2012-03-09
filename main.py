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

class MainHandler(webapp.RequestHandler):
  
  def render_json(self, obj):
    self.response.headers["Content-Type"] = 'text/javascript'
    if self.request.get("callback"):
      self.response.out.write(self.request.get("callback") + "(" + simplejson.dumps(obj) + ")")
    else:
      self.response.out.write(simplejson.dumps(obj))
    
  def get(self):
    site_url = self.request.get("url")
    if site_url:
      feeds = memcache.get(site_url)
      if feeds is not None:
        # good
        self.render_json(feeds)
      else:
        try:
          result = urlfetch.fetch(url=site_url, deadline=10)
          parser = LinkExtractor()
          parser.set_base_url(site_url)
          parser.feed(result.content)
          feeds  = parser.links
          if not feeds:
              # Let's check if by any chance this is actually not a feed?
              data = feedparser.parse(result.content)
              mimeType = "application/atom+xml"
              href = site_url
              if re.match("atom", data.version):
                  mimeType = "application/atom+xml"
              feeds = [{'title': data.feed.title, 'rel': 'self', 'type': mimeType, 'href': href}]
              
          if not memcache.add(site_url, feeds, 604800):
            logging.error("Memcache set failed.")
          self.render_json(feeds)
        except:
          self.render_json([])
          
    else:
      self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'templates', "index.html"), {}))
      
def main():
  application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
