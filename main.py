#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import tornado.web
import os
import psycopg2
import hashlib
from tornado.web import asynchronous
import urllib.parse
from commandprocessor import CommandProcessor, Lord

connectionString = "dbname=postgres user=game password=Abatta"

templateLord = '<div class="lordsay">%s</div>'
templateToLord = '<div class="othersay">%s</div>'
line = '<div class="line"></div>'

cp = CommandProcessor()


def registerlord(lordname, passhash, name, town):
    conn = psycopg2.connect(connectionString)
    cur = conn.cursor()
    cur.callproc("game.register", (lordname, passhash, name, town))
    conn.commit()
    cur.close()
    conn.close()


def haslord(lord):
    res = True
    conn = psycopg2.connect(connectionString)
    cur = conn.cursor()
    cur.execute("select count(1) from lords where name = %s", (lord,))
    result = cur.fetchone()
    if result and result[0] > 0:

        res = True
    else:
        res = False
    cur.close()
    conn.close()            
    return res
    
    
def getAuth(lord, passhash):
    conn = psycopg2.connect(connectionString)
    cur = conn.cursor()
    if  lord and passhash:
        cur.execute("select count(1) from game.lords where name = %s and passhash = %s", (lord, passhash))
    
        result = cur.fetchone()
        if result and result[0] > 0:
            cur.close()
            conn.close()
            return True
    cur.close()
    conn.close()
    return False



    
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        lord_name = self.get_secure_cookie("lord")
        lord_pass = self.get_secure_cookie("passhash")
        if lord_name and lord_pass:
            lord_pass = lord_pass.decode('utf-8')
            lord_name = lord_name.decode('utf-8')
            if not getAuth(lord_name, lord_pass): return None 
            return self.get_secure_cookie("lord")
        return None
    
        
class MainHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        lordName = self.get_secure_cookie("lord").decode('utf-8')
        buildings = cp.data.getLordBuildings(lordName)
        heroes = cp.data.getLordHeroes(lordName)
        lordData = cp.data.getLord(lordName)
        town = lordData['town_name']
        lord = Lord(lordData)
        self.render('index.html', buildings=buildings, townName=town, heroes=heroes, lord=lord)

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')
    def post(self):
        lord_name = self.get_argument("name")
        lord_pass = hashlib.md5(self.get_argument("password").encode('utf-8')).hexdigest()    
        if getAuth(lord_name, lord_pass):
            self.set_secure_cookie("lord", lord_name)
            self.set_secure_cookie("passhash", lord_pass)
            self.redirect("/")
        else:
            self.redirect("/login")
        
        
class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("lord")
        self.clear_cookie("passhash")
        self.redirect("/login")
        

class GetInfoHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        type = self.get_argument("type")
        itemId = self.get_argument("id")
        if type == 'hero':
            hero = cp.data.getHero(itemId)
            self.content_type = 'application/json'
            html = self.render_string('infoForm.html', data=hero).decode('utf-8')
            self.write({'html':html})
            
class SayHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        lord_name = self.get_secure_cookie("lord").decode('utf-8')
        forwho = 'town'
        responses = []
        response = { 'sayTo': forwho, 'answers': [], 'buildings':[], 'heroes':[] }
        for txt in cp.data.getMessages(lord_name):
            if txt == 'update_buildings':
                response['buildings'] = [b.html for b in  cp.data.getLordBuildings(lord_name)]
            else:
                response['answers'].append(templateToLord % txt)
        
        heroAnswers = cp.data.getHeroMessages(lord_name)
        for txt in heroAnswers:
            responses.append({'sayTo': txt, 'answers': [templateToLord % txt for txt in heroAnswers[txt]]}) 
        
        self.content_type = 'application/json'
        if response['buildings'] or response['answers'] or len(responses) > 0:
            self.write({ 'data' : [response] + responses })
        else:
            self.write({})
    
    @tornado.web.authenticated
    def post(self):
        text = self.get_argument("say")
        forwho = self.get_argument("phraseTo", "town", strip=True)
        lord_name = self.get_secure_cookie("lord").decode('utf-8')
        response = cp.processCommand(lord_name, text, forwho)
        res = { 'sayTo': forwho, 'answers': [], 'buildings':[], 'heroes':[] }
        self.content_type = 'application/json'
        res['answers'] = [templateLord % text + line, ]
        for resp in response:
            if resp.type == 'answer':
                res['answers'].append(templateToLord % resp.text)
            elif resp.type == 'update':
                if resp.text == 'buildings':
                    res['buildings'] = \
                        [building.html for building in cp.data.getLordBuildings(lord_name)]
                elif resp.text == 'hero':
                    res['heroes'] = \
                        [hero.html for hero in cp.data.getLordHeroes(lord_name)]
        self.write({"data" : [ res, ] })

        
class Register(BaseHandler):
    def get(self):
        if(len(self.request.arguments) == 3):
            try:
                lord_name = self.get_argument("lordname") 
                name = self.get_argument("name")
                town = self.get_argument("town")
                self.render('register.html', lordname=lord_name, name=name, town=town)
            except:
                self.render('register.html', name="", lordname="", town="")
        else:
            self.render('register.html', name="", lordname="", town="")
        
    def post(self):
        lord_name = self.get_argument("lordname")
        lord_pass = hashlib.md5(self.get_argument("password").encode('utf-8')).hexdigest()    
        name = self.get_argument("name")
        town = self.get_argument("town")
        if haslord(lord_name):
            lord_name = urllib.parse.quote(lord_name)
            name = urllib.parse.quote(name)
            town = urllib.parse.quote(town)
            
            self.redirect('/register?lordname=' + lord_name + '&name=' + name + '&town=' + town)
        else:
            registerlord(lord_name, lord_pass, name, town)
            self.set_secure_cookie("lord", lord_name)
            self.set_secure_cookie("passhash", lord_pass)
            self.redirect("/")

                    
application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/login", LoginHandler),
    (r"/say", SayHandler),
    (r"/register", Register),
    (r"/logout", LogoutHandler),
    (r"/getinfo", GetInfoHandler),
    ],
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    login_url="/login",
    cookie_secret="61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo="
    )

application.listen(8888, "")  # "192.168.1.125")
tornado.ioloop.IOLoop.instance().start()
