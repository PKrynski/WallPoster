# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, session
from uuid import uuid4
import random, string, datetime, hashlib

app_url = ''  # /krynskip/wallposter
app = Flask(__name__)
app.secret_key = 'Wl&(2WB*!NG(C#RAGU$#B'

userList = {}
posts = {}
userPosts = {}

from werkzeug.debug import DebuggedApplication

app.debug = True
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)


def userEnter(username):
    session['uid'] = uuid4()
    session['username'] = username

    try:
        links = userPosts[username]
    except KeyError:
        userPosts[username] = []
        return render_template('no_links.html', username=username, app=app_url)

    return render_template('login_success.html', username=username, links=links, app=app_url)


@app.route(app_url + '/')
def index():
    if 'username' not in session:
        return redirect(app_url + '/login')

    username = session['username']
    try:
        links = userPosts[username]
        return render_template('login_success.html', username=username, links=links, app=app_url)
    except KeyError:
        return render_template('no_links.html', username=username, app=app_url)


@app.route(app_url + '/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register_form.html', app=app_url)

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        conditions = [lambda s: any(c.isupper() for c in s),
                      lambda s: any(c.islower() for c in s),
                      lambda s: any(c.isdigit() for c in s),
                      lambda s: len(s) > 7]

        if username not in userList:

            if password == password2 and all(cond(password) for cond in conditions):
                salt = ''.join(random.sample(string.ascii_letters, 2))
                hashed = hashlib.sha256(salt + password)
                secret = hashed.digest()

                userList[username] = salt + secret
                return render_template('register_success.html', username=username, app=app_url)

        return render_template('register_fail.html', app=app_url)


@app.route(app_url + '/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login_form.html', app=app_url)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in userList:

            userpass = userList[username]
            salt = userpass[:2]

            hashed = hashlib.sha256(salt + password)
            secret = hashed.digest()

            if secret == userpass[2:]:
                template = userEnter(username)
                return template

        return render_template('login_failure.html', app=app_url)


@app.route(app_url + '/newpost', methods=['POST'])
def newpost():
    if 'username' not in session:
        return redirect(app_url + '/login')
    username = session['username']

    currentpost = request.form.get('mypost')

    if currentpost:

        randomID = uuid4()
        newID = str(randomID)[:8]

        post_time = datetime.datetime.now().strftime(" %H:%M:%S %d-%m-%Y")
        # print post_time
        currentpost += post_time

        posts[newID] = currentpost
        try:
            userPosts[username].append(newID)
        except KeyError:
            userPosts[username] = []
            userPosts[username].append(newID)

        return render_template('newpost_complete.html', newID=newID, app=app_url)
    # return "URL: " + currentpost + " newposted to: " + newID

    else:
        return "No URL specified"


@app.route(app_url + '/p/<short>')
def move(short):
    if short in posts:
        content = posts.get(short)
        date = content[-20:]
        post = content[:-20]
        return render_template('mypost.html', post=post, date=date, app=app_url)

    return "Przykro mi, ale wpis: '" + short + "' nie istnieje :("


@app.route(app_url + '/logout')
def logout():
    session.pop('username', None)
    return redirect(app_url + '/login')


if __name__ == '__main__':
    app.run()