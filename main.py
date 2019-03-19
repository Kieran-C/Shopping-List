import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db

import jinja2
import webapp2
from flask import Flask, request, render_template
import bottle
import cgi

app = Flask(__name__)

class ShoppingList(db.Model):
    author = db.UserProperty(indexed=True)
    content = db.StringProperty(multiline=True, indexed=True)

def list_key(list_name=None):
  """Constructs a datastore key for a Guestbook entity with guestbook_name."""
  return db.Key.from_path('Shopping List', list_name or 'default_list')


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('<h1><center>Shopping List</center></h1>')
        user = users.get_current_user()
        if user:
            nickname = user.nickname()
            logout_url = users.create_logout_url('/')
            greeting = '<center>Welcome, {}! <a href="{}">Sign out</a></center>'.format(nickname, logout_url)
            self.response.out.write(greeting)

        else:
            self.redirect(users.create_login_url(self.request.uri))
        self.response.out.write('<html><body>')

        list_name=self.request.get('list_name')
        items = ShoppingList.gql(
            "WHERE ANCESTOR IS :1 AND author = :2 ORDER BY content",
            list_key(list_name), users.get_current_user())

        local_list = []
        for item in items:
            view_item = cgi.escape(item.content)
            if view_item not in local_list:
                local_list.append(view_item)
                self.response.out.write('<blockquote><center>%s</center></blockquote>' %
                                    view_item)


        # Write the submission form and the footer of the page
        self.response.out.write("""
              <form action="/list" method="post">
                <div><center><textarea name="content" rows="1" cols="30" placeholder="Item to Add"></textarea></center></div>
                <div><center><input type="submit" name = "add" value="Add Item">
                </center></div>
              </form>
              <form action="/delete" method="post">
              <div><center><input type="submit" name = "delete" value="Delete an Item"></center></div>
              </form>
              <form action="/edit" method="post">
              <div><center><input type="submit" name = "edit" value="Edit an Item"></center></div>
              </form>
              <form action="/deleteAll" method="post">
                <div><center><input type="submit" name = "clear" value="Delete All"></center></div>
              </form>
            </body>
          </html>""")

class List(webapp2.RequestHandler):
    def post(self):
        list_name = self.request.get('list_name')
        S_list = ShoppingList(parent=list_key(list_name))

        if users.get_current_user():
          S_list.author = users.get_current_user()

        S_list.content = self.request.get('content')
        S_list.put()

        self.redirect('/?' + urllib.urlencode({'list_name': list_name}))

class DeleteHandler(webapp2.RequestHandler):
    def post(self):
        self.response.out.write("""<html><body>
              <h1><center>Shopping List</center></h1>
              <form action="/deleteItem" method="post">
                <div><center><textarea name="content" rows="1" cols="30" placeholder="Item to Delete"></textarea></center></div>
                <div><center><input type="submit" name = "delete" value="Delete Item"></center></div>
              </form>
            </body>
          </html>""")

class DeleteItem(webapp2.RequestHandler):
    def post(self):
        list_name = self.request.get('list_name')
        delEntity = self.request.get('content')
        currentUser = users.get_current_user()
        key = db.GqlQuery("SELECT __key__ FROM ShoppingList WHERE content = :1 AND author = :2", delEntity, currentUser)
        db.delete(key)
        self.redirect('/?' + urllib.urlencode({'list_name': list_name}))

class EditHandler(webapp2.RequestHandler):
    def post(self):
        self.response.out.write("""<html><body>
              <h1><center>Shopping List</center></h1>
              <form action="/EditItem" method="post">
                <div><center><textarea name="old_content" rows="1" cols="30" placeholder="Original Item"></textarea></center></div>
                <div><center><textarea name="new_content" rows="1" cols="30" placeholder="Updated Item"></textarea></center></div>
                <div><center><input type="submit" name = "Edit" value="Update Item"></center></div>
              </form>
            </body>
          </html>""")

class EditItem(webapp2.RequestHandler):
    def post(self):
        list_name = self.request.get('list_name')
        S_list = ShoppingList(parent=list_key(list_name))
        delEntity = self.request.get('old_content')
        addEntity = self.request.get('new_content')
        currentUser = users.get_current_user()
        key = db.GqlQuery("SELECT __key__ FROM ShoppingList WHERE content = :1 AND author = :2", delEntity, currentUser)
        db.delete(key)
        if users.get_current_user():
          S_list.author = users.get_current_user()
        S_list.content = addEntity
        S_list.put()
        self.redirect('/?' + urllib.urlencode({'list_name': list_name}))

class DeleteAll(webapp2.RequestHandler):
    def post(self):
        list_name = self.request.get('list_name')
        currentUser = users.get_current_user()
        key = db.GqlQuery("SELECT __key__ FROM ShoppingList WHERE author = :1", currentUser)
        db.delete(key)
        self.redirect('/?' + urllib.urlencode({'list_name': list_name}))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/list', List),
    ('/delete', DeleteHandler),
    ('/deleteItem', DeleteItem),
    ('/edit', EditHandler),
    ('/EditItem', EditItem),
    ('/deleteAll', DeleteAll)
], debug = True)
