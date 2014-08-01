# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'
MEM1 = 'brian'
MEM2 = 'jc'

# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.



def writeTemplate(self,template,template_values='',allowed=False):
    user = users.get_current_user()
        
    if not user :
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
        user_text = 'Guest'
        validity = False
    else:
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        user_text = user.nickname()
        validity = True
    
    user_values = {
        'user_text': user_text,
        'url': url,
        'url_linktext': url_linktext,
    }

    header = JINJA_ENVIRONMENT.get_template('header.html')
    self.response.write(header.render(user_values))
    
    if validity:
        self.response.write(template.render(template_values))
    else:
        if allowed:
            self.response.write(template.render(template_values))
        else:
            invalid = JINJA_ENVIRONMENT.get_template('invalid.html')
            self.response.write(invalid.render(user_values))


def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Guestbook', guestbook_name)


#
#
#   Home
#
#

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        writeTemplate(self,template,template_values,True)
        
# [END main_page]

#
#
#   MODULE - 1 / Profile
#
#

class Greeting(ndb.Model):
    """Models an individual Guestbook entry with author, content, and date."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


class Guestbook(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        name=guestbook_name
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}

        if name==MEM1 :
            self.redirect('/module-1/1?' + urllib.urlencode(query_params))
        elif name==MEM2 :
            self.redirect('/module-1/2?' + urllib.urlencode(query_params))
        else:
            self.redirect('/?' + urllib.urlencode(query_params))


class MemberOnePage(webapp2.RequestHandler):
    def get(self):

        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(MEM1)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        template_values = {
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
            'name' : MEM1
        }

        template = JINJA_ENVIRONMENT.get_template('profile/member_one.html')
        self.response.write(template.render(template_values))

class MemberTwoPage(webapp2.RequestHandler):
    def get(self):
        
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(MEM2)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
            'name' : MEM2
        }

        template = JINJA_ENVIRONMENT.get_template('profile/member_two.html')
        self.response.write(template.render(template_values))


#
#
#   MODULE - 2 / Thesis Manager
#
#

class Thesis(ndb.Model):
    title = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    status = ndb.StringProperty(indexed=False)
    schoolyear = ndb.StringProperty(indexed=False)

class ThesisNewHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template("thesis/add_thesis.html")
        writeTemplate(self,template)

    def post(self):
        thesis = Thesis()
        thesis.title = self.request.get('title')
        thesis.description = self.request.get('description')
        thesis.schoolyear = self.request.get('syear')
        thesis.status = self.request.get('status')
        thesis.put()
        self.redirect('/thesis/success')

class ThesisSuccessHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('thesis/success.html')
        writeTemplate(self,template)

class ThesisListHandler(webapp2.RequestHandler):
    def get(self):
        
        thesis = Thesis.query().fetch()    
        result = False
        if len(thesis) != 0:
            result = True

        template_values = {
            "all_thesis": thesis,
            "result" : result,
        }

        template = JINJA_ENVIRONMENT.get_template('thesis/list_thesis.html')
        writeTemplate(self,template,template_values,True)

class ThesisViewHandler(webapp2.RequestHandler):
    def get(self, id):
        thesis = Thesis.get_by_id(long(id))
        template_values = {
            "thesis" : thesis,
        }

        if thesis is None:
            template = JINJA_ENVIRONMENT.get_template('error_view.html')
        else:
            template = JINJA_ENVIRONMENT.get_template('thesis/thesis_profile.html')
        
        writeTemplate(self, template, template_values,True)

class ThesisEditHandler(webapp2.RequestHandler):
    def get(self,id):
        thesis = Thesis.get_by_id(long(id))
        template_values = {
            'thesis' : thesis,
        }

        if thesis is None:
            template = JINJA_ENVIRONMENT.get_template('error_view.html')
        else:
            template = JINJA_ENVIRONMENT.get_template('thesis/edit_thesis.html')

        writeTemplate(self,template,template_values)        

    def post(self,id):
        thesis = Thesis.get_by_id(long(id))
        thesis.title = self.request.get('title')
        thesis.description = self.request.get('description')
        thesis.schoolyear = self.request.get('syear')
        thesis.status = self.request.get('status')
        thesis.put()
        self.redirect('/thesis/success')

#
#
#   MODULE - 3 / Adviser
#
#

class Adviser(ndb.Model):
    title = ndb.StringProperty(indexed=False)
    fname = ndb.StringProperty(indexed=False)
    lname = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)
    phone = ndb.StringProperty(indexed=False)
    department = ndb.StringProperty(indexed=False)

class AdviserNewHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('adviser/add_adviser.html')
        writeTemplate(self,template)

    def post(self):
        adviser = Adviser()
        adviser.title = self.request.get('title')
        adviser.fname = self.request.get('fname')
        adviser.lname = self.request.get('lname')
        adviser.email = self.request.get('email')
        adviser.phone = self.request.get('phone')
        adviser.department = self.request.get('department')
        adviser.put()
        self.redirect('/adviser/success')
        
class AdviserListHandler(webapp2.RequestHandler):
    def get(self):
        adviser = Adviser.query().fetch()    
        result = False
        if len(adviser) != 0:
            result = True

        template_values = {
            "all_adviser": adviser,
            "result" : result
        }

        template = JINJA_ENVIRONMENT.get_template('adviser/list_adviser.html')
        writeTemplate(self,template,template_values,True)

class AdviserSuccessHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('adviser/success.html')
        writeTemplate(self,template)

class AdviserViewHandler(webapp2.RequestHandler):
    def get(self, id):
        adviser = Adviser.get_by_id(long(id))
        template_values = {
            "adviser" : adviser
        }

        if adviser is None:
            template = JINJA_ENVIRONMENT.get_template('error_view.html')
        else:
            template = JINJA_ENVIRONMENT.get_template('adviser/adviser_profile.html')
        
        writeTemplate(self,template,template_values,True)

class AdviserEditHandler(webapp2.RequestHandler):
    def get(self,id):
        adviser = Adviser.get_by_id(long(id))
        template_values = {
            'adviser' : adviser
        }

        if adviser is None:
            template = JINJA_ENVIRONMENT.get_template('error_view.html')
        else:
            template = JINJA_ENVIRONMENT.get_template('adviser/edit_adviser.html')

        writeTemplate(self,template,template_values)        

    def post(self,id):
        adviser = Adviser.get_by_id(long(id))
        adviser.title = self.request.get('title')
        adviser.fname = self.request.get('fname')
        adviser.lname = self.request.get('lname')
        adviser.email = self.request.get('email')
        adviser.phone = self.request.get('phone')
        adviser.department = self.request.get('department')
        adviser.put() 
        self.redirect('/adviser/success')
#
#
#   Module - 3 / Student
#
#

class Student(ndb.Model):
    student_number = ndb.StringProperty(indexed=False)
    fname = ndb.StringProperty(indexed=False)
    lname = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)
    phone = ndb.StringProperty(indexed=False)
    department = ndb.StringProperty(indexed=False)

class StudentNewHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('student/add_student.html')
        writeTemplate(self,template)

    def post(self):
        student = Student()
        student.student_number = self.request.get('student_number')
        student.fname = self.request.get('fname')
        student.lname = self.request.get('lname')
        student.email = self.request.get('email')
        student.phone = self.request.get('phone')
        student.department = self.request.get('department')
        student.put()
        self.redirect('/student/success')
        
class StudentListHandler(webapp2.RequestHandler):
    def get(self):
        student = Student.query().fetch()    
        result = False
        if len(student) != 0:
            result = True

        template_values = {
            "all_student": student,
            "result" : result
        }

        template = JINJA_ENVIRONMENT.get_template('student/list_student.html')
        writeTemplate(self,template,template_values,True)

class StudentSuccessHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('student/success.html')
        writeTemplate(self,template)

class StudentViewHandler(webapp2.RequestHandler):
    def get(self, id):
        student = Student.get_by_id(long(id))
        template_values = {
            "student" : student
        }

        if student is None:
            template = JINJA_ENVIRONMENT.get_template('error_view.html')
        else:
            template = JINJA_ENVIRONMENT.get_template('student/student_profile.html')
        
        writeTemplate(self,template,template_values,True)

class StudentEditHandler(webapp2.RequestHandler):
    def get(self,id):
        student = Student.get_by_id(long(id))
        template_values =  {
            'student' : student
        }
        if student is None :
            template = JINJA_ENVIRONMENT.get_template('error_view.html')
        else:
            template = JINJA_ENVIRONMENT.get_template('student/edit_student.html')

        writeTemplate(self,template,template_values)

    def post(self,id):
        student = Student.get_by_id(long(id))
        student.student_number = self.request.get('student_number')
        student.fname = self.request.get('fname')
        student.lname = self.request.get('lname')
        student.email = self.request.get('email')
        student.phone = self.request.get('phone')
        student.department = self.request.get('department')
        student.put()
        self.redirect('/student/success')

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
    ('/module-1/1',MemberOnePage),
    ('/module-1/2',MemberTwoPage),
    ('/thesis/new', ThesisNewHandler),
    ('/thesis/success',ThesisSuccessHandler),
    ('/thesis/list', ThesisListHandler),
    ('/thesis/view/(\d+)', ThesisViewHandler),
    ('/thesis/edit/(\d+)', ThesisEditHandler),
    ('/adviser/new', AdviserNewHandler),
    ('/adviser/list', AdviserListHandler),
    ('/adviser/view/(\d+)', AdviserViewHandler),
    ('/adviser/edit/(\d+)', AdviserEditHandler),
    ('/adviser/success', AdviserSuccessHandler),
    ('/student/new', StudentNewHandler),
    ('/student/list', StudentListHandler),
    ('/student/view/(\d+)', StudentViewHandler),
    ('/student/edit/(\d+)', StudentEditHandler),
    ('/student/success', StudentSuccessHandler),
], debug=True)
