import webapp2

class HeyPage(webapp2.RequestHandler):
  def get(self):
      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write('Hello, All!')

app = webapp2.WSGIApplication([('/hello', HeyPage)],
                              debug=True)
