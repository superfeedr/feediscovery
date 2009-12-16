from sgmllib import SGMLParser

class LinkExtractor(SGMLParser):
  
    def reset(self):  
        SGMLParser.reset(self)
        self.links = []
    
    def start_link(self, attrs):
        if not ('rel', 'alternate') in attrs: return
        if('type', 'application/rss+xml') in attrs: 
          self.links.append(dict(attrs))
        if('type', 'application/atom+xml') in attrs: 
          self.links.append(dict(attrs))
    

