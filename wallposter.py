# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, session, abort
from uuid import uuid4
import random, string, datetime, hashlib, time

app_url = ''  # /krynskip/wallposter
app = Flask(__name__)
app.secret_key = 'Wl&(2WB*!NG(C#RAGU$#B'

userPassList = {}
allPosts = {}
posters = {}
subjects = {}
userPosts = {}
failedLogins = {}
tokens = []


# from werkzeug.debug import DebuggedApplication

# app.debug = True
# app.wsgi_app = DebuggedApplication(app.wsgi_app, False)


def prepareTokens():

    for i in range(20):
        token = uuid4()
        tokens.append(str(token))

prepareTokens()

def userEnter(username):
    session['uid'] = uuid4()
    session['username'] = username

    alldata = showAllPosts()

    try:
        links = userPosts[username]
        allpostsubjects = []
        for link in links:
            allpostsubjects.append(subjects.get(link))
    except KeyError:
        userPosts[username] = []
        return render_template('no_links.html', username=username, alldata=alldata, app=app_url)

    return render_template('login_success.html', username=username, data=zip(links, allpostsubjects),
                           alldata=alldata, app=app_url)


def isPassCorrect(username, password):
    if username in userPassList:

        userpass = userPassList[username]
        salt = userpass[:2]

        secret = hashlib.pbkdf2_hmac('sha256', password, salt, 100000)

        if secret == userpass[2:]:
            return True
    return False


def updatePass(username, password, password2):
    conditions = [lambda s: any(c.isupper() for c in s),
                  lambda s: any(c.islower() for c in s),
                  lambda s: any(c.isdigit() for c in s),
                  lambda s: len(s) > 7]

    if password == password2 and all(cond(password) for cond in conditions):
        salt = ''.join(random.sample(string.ascii_letters, 2))

        secret = hashlib.pbkdf2_hmac('sha256', password, salt, 100000)

        userPassList[username] = salt + secret
        return True

    return False


def showAllPosts():
    title = []
    post = []
    author = []
    date = []

    for item in allPosts:
        title.append(subjects.get(item))
        content = allPosts.get(item)
        single_date = content[-20:]
        single_post = content[:-20]
        post.append(single_post)
        date.append(single_date)
        author.append(posters.get(item))

    alldata = zip(title, post, author, date)

    return alldata


@app.route(app_url + '/')
def index():

    if len(tokens) < 10:
        prepareTokens()

    if 'username' not in session:
        return redirect(app_url + '/login')

    username = session['username']

    alldata = showAllPosts()

    try:
        links = userPosts[username]
        allpostsubjects = []
        for link in links:
            allpostsubjects.append(subjects.get(link))

        return render_template('login_success.html', username=username,
                               data=zip(links, allpostsubjects), alldata=alldata, app=app_url)
    except KeyError:
        return render_template('no_links.html', username=username, alldata=alldata, app=app_url)


@app.route(app_url + '/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register_form.html', app=app_url)

    if request.method == 'POST':

        username = request.form.get('username')

        if any(char in string.punctuation for char in username):
            return render_template('register_fail.html', app=app_url)
        else:

            password = request.form.get('password')
            password2 = request.form.get('password2')

            if username not in userPassList:

                if updatePass(username, password, password2):
                    failedLogins[username] = 0
                    return render_template('register_success.html', username=username, app=app_url)

        return render_template('register_fail.html', app=app_url)


@app.route(app_url + '/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login_form.html', app=app_url)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if isPassCorrect(username, password):
            template = userEnter(username)
            failedLogins[username] = 0
            return template

        try:
            failedLogins[username] += 1
        except KeyError:
            return render_template('login_failure.html', app=app_url)

        if failedLogins[username] > 2:
            time.sleep(3)

        return render_template('login_failure.html', app=app_url)


@app.route(app_url + '/changepass', methods=['GET', 'POST'])
def changePassword():
    if request.method == 'GET':
        return render_template('changepass_form.html', app=app_url)

    if request.method == 'POST':

        username = session['username']
        oldpassword = request.form.get('oldpassword')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if isPassCorrect(username, oldpassword):

            if updatePass(username, password, password2):
                return render_template('changepass_success.html', username=username, app=app_url)

        return render_template('changepass_fail.html', app=app_url)


@app.route(app_url + '/newpost', methods=['POST'])
def newpost():
    if 'username' not in session:
        return redirect(app_url + '/login')
    username = session['username']

    currentpost = request.form.get('mypost')
    postsubject = request.form.get('postsubject')

    if currentpost and postsubject:

        randomID = uuid4()
        newID = str(randomID)[:8]

        post_time = datetime.datetime.now().strftime(" %H:%M:%S %d-%m-%Y")
        currentpost += post_time

        allPosts[newID] = currentpost
        subjects[newID] = postsubject
        posters[newID] = username

        try:
            userPosts[username].append(newID)
        except KeyError:
            userPosts[username] = []
            userPosts[username].append(newID)

        return render_template('newpost_complete.html', newID=newID, app=app_url)

    else:
        return abort(400)


@app.route(app_url + '/p/<short>')
def move(short):
    if short in allPosts:

        title = subjects.get(short)
        content = allPosts.get(short)
        author = posters.get(short)
        date = content[-20:]
        post = content[:-20]
        token = None
        isHidden = "hidden"

        if 'username' in session:
            username = session['username']

            if username == author:
                token = random.choice(tokens)
                isHidden = ""

        return render_template('mypost.html', title=title, post=post, author=author,
                               date=date, id=short, token=token, isHidden=isHidden, app=app_url)

    return abort(404)


@app.route(app_url + '/delete/<short>')
def deletePost(short):
    token = request.args.get('token')

    if token in tokens:

        try:
            del allPosts[short]
            del posters[short]
            del subjects[short]
            userPosts[session['username']].remove(short)
            tokens.remove(token)

        except KeyError:
            return abort(403)

        return render_template('deleted.html', app=app_url)

    return redirect(app_url + '/')


@app.route(app_url + '/logout')
def logout():
    session.pop('username', None)
    return redirect(app_url + '/login')


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=9070)     # for apache ssl
    app.run()
