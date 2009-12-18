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

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template

from django.utils import simplejson

import extractlinks
from extractlinks import LinkExtractor 

class MainHandler(webapp.RequestHandler):
  
  def render_json(self, obj):
    self.response.headers["Content-Type"] = 'text/javascript'
    if self.request.get("callback"):
      self.response.out.write(self.request.get("callback") + "(" + simplejson.dumps(obj) + ")")
    else:
      self.response.out.write(simplejson.dumps(obj))
    
  def get(self):
    if self.request.get("url"):
      try:
        result = urlfetch.fetch(url=self.request.get("url"), deadline=10)
        parser = LinkExtractor()
        parser.feed(result.content)
        self.render_json(parser.links)
      except:
        self.render_json([])
          
    else:
      self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'templates', "index.html"), {}))
      
def main():
  application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
