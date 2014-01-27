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

import os
from google.appengine.ext.webapp import template


USER_RE  = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE  = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

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
        <td><input type="password" name="vpassword" >
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

class MainHandler(webapp2.RequestHandler):
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
        if not valid_username(iun):
            unerr    = "That's not a valid username." 
        ipass    = self.request.get('password')
        ivpass   = self.request.get('vpassword')
        if ipass != ivpass:
            vpasserr = "Your passwords didn't match." 
        elif not valid_password(ipass):
            passerr  = "That wasn't a valid password." 
        iemail   = self.request.get('email')
        if iemail != "" and not valid_email(iemail):
            emailerr = "That's not a vaild email." 
        if vpasserr == "" and passerr == "" and vpasserr == "" and emailerr == "":
            self.redirect("/welcome?username="+iun)
        else:
            iun = escape_html(iun)
            iemail = escape_html(iemail)
            self.write_form(iun,unerr,passerr,vpasserr,iemail,emailerr)

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            path = os.path.join(os.path.dirname(__file__), 'welcome.html')
            self.response.write(template.render(path,{"username": username}))
        else:
            self.redirect('/')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/welcome', WelcomeHandler)
], debug=True)
