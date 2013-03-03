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
import webapp2
import json

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template

import extractlinks
from extractlinks import LinkExtractor
import feedparser
import re
import urlparse

class MainHandler(webapp2.RequestHandler):

  def render_json(self, obj):
    self.response.headers["Content-Type"] = 'text/javascript'
    if self.request.get("callback"):
      self.response.write(self.request.get("callback") + "(" + json.dumps(obj) + ")")
    else:
      self.response.write(json.dumps(obj))

  # Correct feed urls with rel="self" and add hubs
  def extend_feed(self, feed, links):
    feed_self = next((l for l in links if l['rel'] == 'self'), None)
    if feed_self is not None:
      feed['href'] = feed_self['href']
      feed['type'] = feed_self['type']
    feed['hubs'] = [l for l in links if l['rel'] == 'hub']

  def get(self):
    # We need to clean up the url first and remove any fragment
    site_url = urlparse.urldefrag(self.request.get("url"))[0]
    force = (self.request.get("force").lower()) in ['true', '1']
    extend = (self.request.get("extend").lower()) in ['true', '1']
    feeds = [] # default value

    if site_url:
      feeds = memcache.get(site_url + "." + str(extend))
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
            if data.bozo == 0:
              feed = {'title': data.feed.get('title', ''), 'rel': 'self', 'type': 'application/atom+xml', 'href': site_url}
              links = data.feed.get('links', [])
              if extend:
                self.extend_feed(feed, links)
              feeds = [feed]
          else:
            if extend:
              for f in feeds:
                data = feedparser.parse(f['href'])
                links = data.feed.get('links', [])
                self.extend_feed(f, links)

        except:
          feeds = []

        if not memcache.set(site_url + "." + str(extend), feeds, 86400):
          logging.error("Memcache set failed.")
        else:
          logging.debug("Memcache set.")
        self.render_json(feeds)

    else:
      self.response.write(template.render(os.path.join(os.path.dirname(__file__), 'templates', "index.html"), {}))

app = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
