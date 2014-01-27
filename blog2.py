import webapp2
import os
import re
from string import letters

import jinja2
import logging
import sys
import urllib2
import json
#import queue
from xml.dom import minidom
import time
from time import strftime
from datetime import datetime, timedelta

from google.appengine.ext import db
from google.appengine.api import memcache


from signup import *


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

#blog_key = db.Key.from_path('ASCIIChan','blog')

## queue
class Queue:
    """A sample implementation of a First-In-First-Out
        data structure."""
    def __init__(self):
        self.in_stack = []
        self.out_stack = []
    def push(self, obj):
        self.in_stack.append(obj)
    def pop(self):
        if not self.out_stack:
            self.in_stack.reverse()
            self.out_stack = self.in_stack
            self.in_stack = []
        return self.out_stack.pop()
    def size(self):
        return len(self.in_stack)
    def contents(self):
        return self.in_stack
# From Solution
def age_set(key, val):
    save_time = datetime.utcnow()
    memcache.set(key, (val,save_time))
def age_get(key):
    r = memcache.get(key)
    if r:
        val, save_time = r
        age = (datetime.utcnow() - save_time).total_seconds()
    else:
        val, age = None, 0

    return val, age


cache = Queue()

## database
class dbBlog(db.Model):
    subject=db.StringProperty(required=True)
    content=db.TextProperty(required=True)
    created=db.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a,**kw):
        self.response.out.write(*a,**kw)
    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))
    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.response.out.write(json_txt)


class Newpost(Handler):
  def get(self):
      self.render('newpost.html')

  def post(self):
      global refdbstart
      subject=self.request.get("subject")
      content=self.request.get("content")
      if subject and content:
          b=dbBlog(subject=subject,content=content)
          b_key = b.put()
          error = "blog/%d" % b_key.id()
          self.redirect("/blog/%d" % b_key.id())
          #Initialize time on first post.
          if cache.size() == 0:
              refdbstart = time.clock()
              logging.debug('DEBUG: Reset refdbstart 1 cache size %d', cache.size())
          # Put the entry in the cache.
          cache.push(b)
      else:
          error="We need both the subject and the blog entry."
          self.render('newpost.html',subject=subject,content=content,error=error)

def RefreshCache(self):
    blogs=db.GqlQuery("SELECT * From dbBlog ORDER BY created DESC LIMIT 10")
    logging.debug('DEBUG: Reset refdbstart 2 cache size %d', cache.size())
    for blog in blogs:
        cache.push(blog)

class Blog(Handler):
    def get(self):
        global refdbstart
        if cache.size() == 0:
            blogs=db.GqlQuery("SELECT * From dbBlog ORDER BY created DESC LIMIT 10")
            logging.debug('DEBUG: Reset refdbstart 2 cache size %d', cache.size())
            for blog in blogs:
                cache.push(blog)
            refdbstart = time.clock()
        mqt = time.clock() - refdbstart
        mqt = "%.4f" % mqt
        logging.debug('DEBUG: cache size %d', cache.size())
        self.render("blog.html",blogs=cache.contents(),mainqueried=mqt)

class FlushCache(Handler):
    def get(self):
        global refdbstart
        blogs=db.GqlQuery("SELECT * From dbBlog ORDER BY created DESC LIMIT 10")
        logging.debug('DEBUG: Reset refdbstart 2 cache size %d', cache.size())
        while cache.size() != 0:
            cache.pop()
            #for blog in blogs:
        #cache.push(blog)
        #mqt = 0.0
        #refdbstart = time.clock()
        self.redirect("/blog")
#self.render("blog.html",blogs=cache.contents(),mainqueried=mqt)

class Permalink(Handler):
    def get(self, blog_id):
        global refdbstart
        mqt = time.clock() - refdbstart
        mqt = "%.4f" % mqt
        s = dbBlog.get_by_id(int(blog_id))
        self.render("blog.html",blogs=[s],debug="Permalink",mainqueried=mqt)

# Json - List of dictionaries. Each dictionary contains one entry.
# One entry:
# {"content": "<entry data>", "created": "<date>", "last_modifed": "<date>", "subject": "<subject/title>"}
# str.ftime to format the date.
# HEADER: Content-type: application/json; charset=UTF-8
def createJson(blogs):
    JL = []
    for blog in blogs:
        #entry = {"content": blog.content,"created": time.strftime("%a %b %d %T %Y",blog.created), "last_modifed": time.strftime("%a %b %d %T %Y",blog.created), "subject": blog.subject}
        dt = blog.created.strftime('%Y-%m-%d %H:%M:%S')
        #entry = json.dumps(dict(content=blog.content,created=dt,last_modifed=dt,subject=blog.subject))
        entry = {"content": blog.content, "created": dt, "last_modifed": dt, "subject": blog.subject}
        JL.append(entry)
    return JL

class BlogJson(Handler):
    def get(self):
        blogs=db.GqlQuery("SELECT * From dbBlog ORDER BY created DESC LIMIT 10")
        #json.loads(createJson(blogs))
        self.render_json(createJson(blogs))
    
class PermalinkJson(Handler):
    def get(self, blog_id):
        s = dbBlog.get_by_id(int(blog_id))
        blogs=[s]
        self.render_json(createJson(blogs)[0])


app = webapp2.WSGIApplication([('/blog/newpost', Newpost),
                               ('/blog/signup', SignupHandler),
                               ('/blog/login', LoginHandler),
                               ('/blog/logout', LogoutHandler),
                               ('/blog/welcome', WelcomeHandler),
                               ('/blog', Blog),
                               ('/blog/flush', FlushCache),
                               ('/blog/(\d+)', Permalink),
                               ('/blog/.json', BlogJson),
                               ('/blog/(\d+).json', PermalinkJson)],
                              debug=True)

def main():
    # Set the logging level in the main function
    # See the section on Requests and App Caching for information on how
    # App Engine reuses your request handlers when you specify a main function
    logging.getLogger().setLevel(logging.DEBUG)
    webapp.util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
