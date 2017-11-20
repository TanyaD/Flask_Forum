from flask import Flask, render_template, request, redirect, flash, session
app=Flask(__name__)
app.secret_key='secrlksj'
from mysqlconnection import MySQLConnector
mysql = MySQLConnector(app, 'registrationdb')
import os, binascii
import md5


import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'^([^0-9]*)$')



#display login/registration page
@app.route('/')
def index():
    return render_template('index.html', type1='hidden')

#validate and submit new user registration
@app.route('/wall_post', methods=['POST'])
def pass_data():
    fname= request.form['fname']
    lname= request.form['lname']
    email= request.form['email']
    password= request.form['password']
    password_two= request.form['confirm_password']
    salt =  binascii.b2a_hex(os.urandom(15))
    hashed_pw = md5.new(password + salt).hexdigest()
    
    #firstname validation
    if len(request.form['fname'])<1:
        flash('First Name cannot be empty!')
        return redirect('/')
    if not NAME_REGEX.match(request.form['fname']):
        flash("No numbers accepted in First Name!")
        return redirect('/')
    

    #lastname validation
    if len(request.form['lname']) < 1:
        flash("Last Name cannot be empty!")
        return redirect('/')
    if not NAME_REGEX.match(request.form['lname']):
        flash("No numbers accepted in Last Name!")
        return redirect('/')

    #validate email format
    if len(request.form['email']) < 1:
        flash("Email cannot be empty!")
        return redirect('/')
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Email Address should look like email@email.com!")
        return redirect('/')

    #validate if user already exists
    email_value=request.form['email']
    data = {'email': email_value}
    query = "SELECT email FROM users WHERE email = :email"
    result=mysql.query_db(query, data)
    if result != []:
        flash("Email invalid, user already exists")
        return redirect('/')

    #password validation
    if len(request.form['password']) < 1:
        flash("Pwd cannot be empty!")
        return redirect('/')
    if len(request.form['password']) < 8:
        flash("Password should be more than 8 characters")
        return redirect('/')

    #confirm_password validation
    if len(request.form['confirm_password']) < 1:
        flash("Pwd cannot be empty!")
        return redirect('/')
    if request.form['confirm_password']!=request.form['password']:
        flash("Pwd should match!")
        return redirect('/')

    #post data to DB
    query = "INSERT INTO users (first_name, last_name, email, password, salt) VALUES (:first_name, :last_name, :email, :hashed_pw, :salt)"
    data = {
        'first_name': request.form['fname'],
        'last_name':  request.form['lname'],
        'email': request.form['email'],
        'hashed_pw': hashed_pw,
        'salt': salt
    }
    session['user_id'] = mysql.query_db(query, data)
    return redirect('/wall')

#Loading the Wall on submit, display all messages and comments       
@app.route('/wall')
def sucess():
    if 'user_id' in session:
        query = "SELECT messages.id AS id, messages.message AS message, users.first_name AS first_name, users.last_name AS last_name FROM messages LEFT JOIN users ON users.id = messages.user_id"
        posts = mysql.query_db(query)
        for x in posts:
            x['comments'] = []
            query = "SELECT comments.comment, users.first_name, users.last_name FROM comments LEFT JOIN users ON users.id = comments.user_id WHERE comments.message_id = :message_id"
            data = {
                'message_id': x['id'],
            }
            comments = mysql.query_db(query, data)
            if comments != []:
                x['comments'] = comments
        return  render_template('wall.html', posts=posts)
    return redirect('/')

#Validate and login with existing user  
@app.route('/login', methods=['POST'])
def login():
    email=request.form['login_email']
    password=request.form['login_password']
    user_query = "SELECT * FROM users WHERE users.email = :email LIMIT 1"
    query_data = {'email': email}
    user = mysql.query_db(user_query, query_data)

    if len(request.form['login_email']) < 1:
        flash("Email cannot be empty!")
        return redirect('/')
    if not EMAIL_REGEX.match(request.form['login_email']):
        flash("Email Address should look like email@email.com!")
        return redirect('/')
    if len(request.form['login_password']) < 1:
        flash("Pwd cannot be empty!")
        return redirect('/')

    email_value=request.form['login_email']
    data = {'email': email_value}
    query = "SELECT email FROM users WHERE email = :email"
    result=mysql.query_db(query, data)
    if result == []:
        flash("User is not recognized, please register")
        return redirect('/')

    if user == []:
        flash("User doesn't exist")
        return redirect('/')

    if user[0]['password'] == md5.new(password + user[0]['salt']).hexdigest():
        session['user_id']=user[0]['id']
        return redirect('/wall')
    
    flash("Password invalid")
    return redirect('/')

#Create new message
@app.route('/postmessage', methods=['POST'])
def postMessage():
    if 'user_id' in session:
        message=request.form['message']
        query = "INSERT INTO messages (user_id, message) VALUES (:user_id, :message)"
        data = {
            'user_id': session['user_id'],
            'message': message
        }
        mysql.query_db(query, data)
        return redirect('/wall')
    return redirect('/')

#Create new comment to a message
@app.route('/postcomment', methods=['POST'])
def postComment():
    if 'user_id' in session:
        comment=request.form['comment']
        message_id=request.form['message_id']
        query = "INSERT INTO comments (user_id, message_id, comment) VALUES (:user_id, :message_id, :comment)"
        data = {
                'user_id': session['user_id'],
                'message_id': message_id,
                'comment': comment
            }
        mysql.query_db(query, data)
        return redirect('/wall')
    return redirect('/')


#Logout
@app.route('/logout', methods=['POST'])
def logOut():
    session.pop('user_id')
    return redirect('/')
    





app.run(debug=True)




