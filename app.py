from flask import Flask, render_template, request, url_for, redirect, session
from datetime import datetime
from pathlib import Path
import numpy as np
import uuid
import recognition.load_model as model
import os
import sqlite3
import hashlib
from werkzeug.utils import secure_filename
import pytz
import plotly
import json
import plotly.express as px
import pandas as pd
import re

app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = Path(__file__).resolve().parent/'static/uploaded'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB


def getLoginDetails():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
            totalCO2 = 0
        else:
            loggedIn = True
            cur.execute(
                "SELECT userId, firstName FROM users WHERE email = '" + session['email'] + "'")
            userId, firstName = cur.fetchone()
            cur.execute(
                "SELECT count(productId) FROM kart WHERE userId = " + str(userId))
            noOfItems = cur.fetchone()[0]
            cur.execute("SELECT products.productId, products.name, products.CO2, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = " + str(userId))
            products = cur.fetchall()
            totalCO2 = 0
            for row in products:
                totalCO2 += row[2]
    conn.close()
    return (loggedIn, firstName, noOfItems, totalCO2)


def is_valid(email, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route('/', methods=['GET', 'POST'])
def root():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    if request.method == 'GET':
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT productId, name, CO2, image,categoryId FROM products WHERE categoryId=5 AND image IS NOT '' ")
            data = cur.fetchall()
        conn.close()
        return render_template('index.html', loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, data=data, totalCO2=totalCO2)
    elif request.method == 'POST':
        file = request.files['file']
        if file:
            filename = str(uuid.uuid4())+'_'+file.filename
            file.save(app.config['UPLOAD_FOLDER']/filename)
            model_label = model.recog_pic(filename)
            with sqlite3.connect('database.db') as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT productId, name, CO2 FROM products WHERE model_label=" +
                    str(model_label)
                )
                data = cur.fetchall()
                print(data)
                productId = data[0][0]
                predict = data[0][1]
                carbonM = data[0][2]
            conn.close()
        return render_template('recog_result(practice).html',  predict=predict, carbonM=carbonM, src=url_for('static', filename=f'uploaded/{filename}'), loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, totalCO2=totalCO2, model_label=model_label, productId=productId)


@app.route('/searchbar', methods=['POST'])
def searchbar():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    keyword = request.form['searchbar']
    print(keyword)
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT productId,name,CO2,image,categoryId FROM products WHERE name LIKE '%{}%' AND image IS NOT NULL AND image IS NOT '' AND categoryId !=5 ".format(keyword))
        data = cur.fetchall()

        if len(data) == 0:
            msg = 'Sorry!! No related material'
        else:
            msg = 'We got {} data for you!!'.format(len(data))
    conn.close()
    try:
        new_data = []
        for i in data:
            y = list(i)
            if y[4] == 1:
                y[4] = 'living'
                new_data.append(tuple(y))
            elif y[4] == 2:
                y[4] = 'dessert'
                new_data.append(tuple(y))
            elif y[4] == 3:
                y[4] = 'staple'
                new_data.append(tuple(y))
            elif y[4] == 4:
                y[4] = 'drinks'
                new_data.append(tuple(y))
        pagelink = 'parts/_searchbar.html'
        return render_template('shop-grid2.html', pagelink=pagelink, msg=msg, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, data=new_data, totalCO2=totalCO2)
    except:
        pagelink = 'parts/_searchbar.html'
        return render_template('shop-grid2.html', pagelink=pagelink, msg=msg, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, data=new_data, totalCO2=totalCO2)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            pagelink = 'parts/_login.html'
            return render_template('shop-grid2.html', pagelink=pagelink, error=error)
    elif request.method == 'GET':
        error = 'please enter your account'
        pagelink = 'parts/_login.html'
        return render_template('shop-grid2.html', pagelink=pagelink, error=error)


@app.route('/register', methods=["POST"])
def reg():
    error = 'error'
    if request.method == 'POST':
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address = request.form['address']
        zipcode = request.form['zipcode']
        city = request.form['city']
        country = request.form['country']
        phone = request.form['phone']
        with sqlite3.connect('database.db') as con:
            try:

                cur = con.cursor()
                cur.execute('INSERT INTO users (password, email, firstName, lastName, address, zipcode, city, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (hashlib.md5(
                    password.encode()).hexdigest(), email, firstName, lastName, address, zipcode, city, country, phone))
                con.commit()
                msg = "Registered Successfully"
                print(msg)
            except:
                con.rollback()
                msg = "Error occured"
        con.close()
        pagelink = 'parts/_login.html'
        return render_template('shop-grid2.html', pagelink=pagelink, error=msg)


@app.route("/logout", methods=['GET'])
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))


@app.route('/regform', methods=['GET'])
def registrationform():
    pagelink = 'parts/_register.html'
    return render_template('shop-grid2.html', pagelink=pagelink)


@app.route('/detail', methods=['GET'])
def detail():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    pagelink = "parts/_shop-grid.html"
    return render_template('shop-grid2.html', pagelink=pagelink, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, totalCO2=totalCO2)


@app.route('/living', methods=['GET'])
def living():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT productId, name, CO2, image,categoryId FROM products WHERE categoryId=1 AND image IS NOT '' ")
        data = cur.fetchall()
    conn.close()
    pagelink = "parts/living.html"
    return render_template('shop-grid2.html', pagelink=pagelink, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, data=data, totalCO2=totalCO2)


@app.route('/dessert', methods=['GET'])
def dessert():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT productId, name, CO2, image,categoryId FROM products WHERE categoryId=2")
        data = cur.fetchall()
    conn.close()
    pagelink = "parts/dessert2.html"
    return render_template('shop-grid2.html', pagelink=pagelink, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, data=data, totalCO2=totalCO2)


@app.route('/staple', methods=['GET'])
def staple():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT productId, name, CO2, image,categoryId FROM products WHERE categoryId=3 AND image IS NOT '' ")
        data = cur.fetchall()
    conn.close()
    pagelink = "parts/staple.html"
    return render_template('shop-grid2.html', pagelink=pagelink, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, data=data, totalCO2=totalCO2)


@app.route('/drinks', methods=['GET'])
def drinks():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT productId, name, CO2, image,categoryId,P_type FROM products WHERE categoryId=4 AND image IS NOT '' ")
        data = cur.fetchall()
    conn.close()
    pagelink = "parts/drinks.html"
    return render_template('shop-grid2.html', pagelink=pagelink, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, data=data, totalCO2=totalCO2)


@app.route('/checkout', methods=['GET'])
def checkout():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    pagelink = 'parts/_checkout.html'
    tree = 0
    tree = round(totalCO2/900)
    numtree = range(tree)
    return render_template('shop-grid2.html', pagelink=pagelink, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, totalCO2=totalCO2, tree=tree, numtree=numtree)


@app.route('/about', methods=['GET'])
def about():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    pagelink = 'parts/_about.html'
    utc_now = datetime.utcnow()
    utc_timezone = pytz.timezone('UTC')
    taipei_timezone = pytz.timezone('Asia/Taipei')
    taipei_now = utc_timezone.localize(utc_now).astimezone(
        taipei_timezone).strftime('%Y-%m-%d %H:%M')
    return render_template('shop-grid2.html', pagelink=pagelink, current_time=taipei_now, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, totalCO2=totalCO2)


@app.route('/CNN')
def cnn_model():
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    his = pd.read_csv('training_history_53img_SGD.csv')
    his['epoch'] = list(range(1, 301))
    fig1 = px.line(his, x='epoch', y=['accuracy', 'val_accuracy'], labels={
                   'accuracy': 'training_loss', 'val_loss': 'validation_loss'})
    fig1.data[0].line.color = 'red'
    fig1.data[1].line.color = 'blue'
    fig2 = px.line(his, x='epoch', y=['loss', 'val_loss'], labels={
                   'loss': 'training_loss', 'val_loss': 'validation_loss'})
    fig3 = px.line(his, x='epoch', y='lr', labels={'lr': 'learning_rate'})
    figs = [fig1, fig2, fig3]
    graphJSON = json.dumps(figs, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('./parts/_cnn.html', loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, totalCO2=totalCO2, graphJSON=graphJSON)


@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('login'))
    else:
        productId = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email ='" +
                        session['email'] + "'")
            userId = cur.fetchone()[0]
            cur.execute(
                "SELECT categoryId FROM products WHERE productId={}".format(productId))
            categoryId = cur.fetchone()[0]
            try:
                cur.execute(
                    "INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
                conn.commit()
                msg = "Added successfully"
            except:
                conn.rollback()
                msg = 'Error occured'
        conn.close()
        if categoryId == 1:
            return redirect(url_for('living'))
        elif categoryId == 2:
            return redirect(url_for('dessert'))
        elif categoryId == 3:
            return redirect(url_for('staple'))
        elif categoryId == 4:
            return redirect(url_for('drinks'))
        else:
            return redirect(url_for('root'))


@app.route("/carts")
def cart():
    if 'email' not in session:
        return redirect(url_for('login'))
    loggedIn, firstName, noOfItems, totalCO2 = getLoginDetails()
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute("SELECT products.productId, products.name, products.CO2, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = " + str(userId))
        products = cur.fetchall()
    totalCO2 = 0
    for row in products:
        totalCO2 += row[2]
    pagelink = 'parts/_cart2.html'
    return render_template('shop-grid2.html', pagelink=pagelink, products=products, totalCO2=totalCO2, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    productId = int(request.args.get('productId'))
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        try:
            cur.execute("DELETE FROM kart WHERE userId = " +
                        str(userId) + " AND productId = " + str(productId))
            conn.commit()
            msg = "removed successfully"
        except:
            conn.rollback()
            msg = "error occured"
    conn.close()
    return redirect(url_for('cart'))


@app.route('/clearTheCart')
def clearCart():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM kart')
            conn.commit()
        except:
            conn.rollback()
    conn.close()
    return redirect(url_for('root'))


if __name__ == "__main__":
    app.run(debug=True)
