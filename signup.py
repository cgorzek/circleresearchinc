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
import webapp2
import re
import random
import string
import hashlib
import hmac
import jinja2


import os
from google.appengine.ext.webapp import template
from google.appengine.ext import db
# debugging?
import logging

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

SECRET = 'dajfa;ksdasjdfad878asdjfdas+98'

USER_RE  = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE  = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

logging.getLogger().setLevel(logging.DEBUG)

## functions
def hash_str(s):
    return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

def make_salt():
    return ''.join(random.choice(string.letters) for x in range(5))

def make_pw_hash(name, pw, salt = None ):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)
    
def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)

def valid_username(username):
    return USER_RE.match(username)
def valid_password(password):
    return PASS_RE.match(password)
def valid_email(email):
    return EMAIL_RE.match(email)

def escape_html(s):
    if s == "": return s
    for (i, o) in (("&","&amp;"),
                   (">","&gt;"),
                   ("<","&lt;"),
                   ('"',"&quote;")):
        s = s.replace(i, o)
    return s

form="""
<h2>Signup</h2>
<form method="post">
    <br>
    <table>
      <colgroup>
        <col align="right">
        <col>
        <col style="color: red">
      <tr>
        <td {text-align: right;} align="right">Username:        
        <td><input type="text" name="username"  value="%(username)s"> 
        <td {color: red} style="color: red">%(usererror)s
      <tr>
        <td {text-align: right;} align="right">Password:        
        <td><input type="password" name="password"  > 
        <td {color: red} style="color: red">%(passerror)s
      <tr>
        <td {text-align: right;} align="right">Verify Password: 
        <td><input type="password" name="verify" >
        <td {color: red} style="color: red">%(vpasserror)s
      <tr>
        <td {text-align: right;} align="right">Email address: (optional)   
        <td><input type="text" name="email"     value="%(email)s">
        <td {color: red} style="color: red">%(emailerror)s
    </table>
    <br>
    <br>
    <input type="submit">
</form>
"""

welcomepg="""
<html>
<head> 
<title>Unit 2 Signup </title>
</head>
<body>
<h2>Welcome, %(newuser)s</h2>
</body>
</html>
"""
## database
class dbUser(db.Model):
    username=db.StringProperty(required=True)
    password=db.TextProperty(required=True)
    email=db.TextProperty()
    created=db.DateTimeProperty(auto_now_add=True)

def dbUserfind(u):
    userrecord=db.GqlQuery("SELECT * From dbUser WHERE username = :1", u)
    if not userrecord.get():
        return False
    else:
        return True

def dbUsergetpass(u):
    userrecord=db.GqlQuery("SELECT * From dbUser WHERE username = :1", u)
    #logging.info('dbUsergetpass %s', userrecord.get())
    logging.debug('DEBUG')
    return userrecord.get().password

def dbUserstore(username,password,email):
    e = dbUser(username=username,password=password,email=email)
    e.put()

class Handler(webapp2.RequestHandler):
    def write(self, *a,**kw):
        self.response.out.write(*a,**kw)
    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))

class SignupHandler(webapp2.RequestHandler):
    def write_form(self, username="", usererror="", passerror="", vpasserror="", email="", emailerror=""):
        self.response.write(form % { 
            "username": username, 
            "usererror": usererror, 
            "passerror": passerror, 
            "vpasserror": vpasserror, 
            "email": email, 
            "emailerror": emailerror 
        })


    def get(self):
        self.write_form()

    def post(self):
        unerr    = ""
        passerr  = ""
        vpasserr = ""
        emailerr = ""        
        iun      = self.request.get('username')
        iun = escape_html(iun)
        if not valid_username(iun):
            unerr    = "That's not a valid username."
        if dbUserfind(iun):
            unerr    = "Username already exists."
        ipass    = self.request.get('password')
        ivpass   = self.request.get('verify')
        if ipass != ivpass:
            vpasserr = "Your passwords didn't match." 
        elif not valid_password(ipass):
            passerr  = "That wasn't a valid password." 
        iemail   = self.request.get('email')
        if iemail != "" and not valid_email(iemail):
            emailerr = "That's not a vaild email." 
        if vpasserr == "" and passerr == "" and vpasserr == "" and emailerr == "" and unerr == "":
            secure_pw = make_secure_val(ipass)
            dbUserstore(iun,secure_pw,iemail)
            secure_iun  = make_secure_val(iun)
            hash = make_pw_hash(iun, ipass)
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.headers.add_header('Set-Cookie',str('name=%s; hash="%s"; Path=/' % (secure_iun, hash)))
            self.redirect("/blog/welcome")
        else:
            iun = escape_html(iun)
            iemail = escape_html(iemail)
            self.write_form(iun,unerr,passerr,vpasserr,iemail,emailerr)

class LoginHandler(Handler):
    def write_form(self, username="", usererror="", passerror=""):
        self.render('login-form.html',username=username,usererror=usererror,passerror=passerror)
            #self.response.write(form % {
            #                "username": username,
            #                "usererror": usererror,
            #                "passerror": passerror,
            #                })
    
    
    def get(self):
        self.write_form()
    
    def post(self):
        unerr    = ""
        passerr  = ""
        vpasserr = ""
        iun      = self.request.get('username')
        iun = escape_html(iun)
        if not valid_username(iun):
            unerr    = "That's not a valid username. Typo?"
        if not dbUserfind(iun):
            unerr    = "Username not found."
        ipass    = self.request.get('password')
        secure_pw  = make_secure_val(ipass)
        db_pw = dbUsergetpass(iun)
        if not secure_pw == db_pw:
            passerr    = "Password doesn't match. secure_pw %s db_pw %s" % (secure_pw,db_pw)
        if unerr == "" and passerr == "":
            secure_iun  = make_secure_val(iun)
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.headers.add_header('Set-Cookie',str('name=%s; hash="%s"; Path=/' % (secure_iun, hash)))
            self.redirect("/blog/welcome")
        else:
            iun = escape_html(iun)
            self.write_form(iun,unerr,passerr)

class LogoutHandler(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie',str('name=%s; hash="%s"; Path=/' % ("", "")))
        self.redirect("/blog/signup")


class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        username = check_secure_val(self.request.cookies.get('name'))
        if username == None :
            self.redirect('/blog/signup', unerr="Invalid Cookie.")
        elif not valid_username(username):
            self.redirect('/blog/signup', unerr="Invalud username.")
        elif not dbUserfind(username):
            self.redirect('/blog/signup', unerr="That user already exists.")
        else:
            path = os.path.join(os.path.dirname(__file__), 'welcome.html')
            self.response.write(template.render(path,{"username": username}))


                #app = webapp2.WSGIApplication([
                #                              ('/blog/signup', SignupHandler),
                #                              ('/blog/welcome', WelcomeHandler)
#                              ], debug=True)

#app = webapp2.WSGIApplication([
#('/hw2/signup', MainHandler),
#('/hw2/welcome', WelcomeHandler)
#], debug=True)


