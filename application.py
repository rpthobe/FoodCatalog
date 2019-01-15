from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    url_for,
    flash
)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Course, FoodItem, UserTable
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Course Food Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///mealsDB.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Input user into DB
    output = ''
    if request.method == 'POST':
        user = session.query(UserTable).filter_by(
            email=login_session['email']).one_or_none()
        if not user:
            newUser = UserTable(username=data['name'], email=data['email'])
            session.add(newUser)
            session.commit()

    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; '
    output += 'height: 300px;border-radius: 150px; '
    output += '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?'
    url += 'token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps(
            'Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showCourses'))
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Restaurant Information
@app.route('/restaurant/<int:course_id>/menu/JSON')
def courseFoodItemsJSON(course_id):
    restaurant = session.query(Course).filter_by(id=course_id).one()
    foodItems = session.query(FoodItem).filter_by(
        course_id=course_id).all()
    return jsonify(foodItems=[i.serialize for i in foodItems])


@app.route('/restaurant/<int:course_id>/menu/<int:food_id>/JSON')
def foodItemJSON(course_id, food_id):
    foodItem = session.query(FoodItem).filter_by(id=food_id).one()
    return jsonify(foodItem=foodItem.serialize)


@app.route('/restaurant/JSON')
def coursesJSON():
    courses = session.query(Course).all()
    return jsonify(courses=[r.serialize for r in courses])


# Show/Add all Courses
@app.route('/')
@app.route('/Courses/', methods=['GET', 'POST'])
def showCourses():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        user = session.query(UserTable).filter_by(
            email=login_session['email']).one()
        newCourse = Course(name=request.form['newCourseName'], user_id=user.id)
        session.add(newCourse)
        # flash('New Course %s Successfully Created' % newCourse.name)
        session.commit()
    courses = session.query(Course).order_by(asc(Course.name))
    return render_template('courses.html', courses=courses)


# Show/Add a Food per course
@app.route('/course/<int:course_id>/', methods=['GET', 'POST'])
def showFood(course_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        course = session.query(Course).filter_by(id=course_id).one()
        user = session.query(UserTable).filter_by(
            email=login_session['email']).one()
        newItem = FoodItem(name=request.form['newFoodName'],
                           description=request.form[
                           'newFoodDescription'], course_id=course_id,
                           user_id=user.id)
        session.add(newItem)
        session.commit()
        # flash('New Menu %s Item Successfully Created' % (newItem.name))
        # return redirect(url_for('showFood', course_id=course_id))
    courses = session.query(Course).order_by(asc(Course.name))
    course = session.query(Course).filter_by(id=course_id).one()
    food = session.query(FoodItem).filter_by(course_id=course_id).all()
    return render_template('food.html',
                           food=food, course=course, courses=courses)


# Show a Food Item details/Edit
@app.route('/food/<int:foodItem_id>', methods=['GET', 'POST'])
def showFoodItem(foodItem_id):
    if 'username' not in login_session:
            return redirect('/login')
    user = session.query(UserTable).filter_by(
            email=login_session['email']).one_or_none()
    userFoodItem = session.query(FoodItem.id).filter_by(user_id=user.id).all()
    if not userFoodItem:
            flash('Cannot Edit any food items - '
                  'Can only edit those you have created')
    if request.method == 'POST':
        editedItem = session.query(FoodItem).filter_by(id=foodItem_id).one()
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
    courses = session.query(Course).order_by(asc(Course.name))
    food = session.query(FoodItem).filter_by(id=foodItem_id).one()
    return render_template('foodItem.html', food=food,
                           courses=courses, foodItem=userFoodItem)


# Edit Course Name
@app.route('/course/edit', methods=['GET', 'POST'])
def editCourse():
    if 'username' not in login_session:
            return redirect('/login')
    courses = session.query(Course).order_by(asc(Course.name))
    user = session.query(UserTable).filter_by(
            username=login_session['username']).one_or_none()
    userCourseEdit = session.query(Course).filter_by(user_id=user.id).all()
    if userCourseEdit == []:
            flash('Cannot Edit any Courses - '
                  'Can only edit courses you have created')
    if request.method == 'POST':
        if request.form['courseEdit']:
            course_id = request.form['courseEdit']
            editedItem = session.query(Course).filter_by(id=course_id).one()
            if request.form['editedName']:
                editedItem.name = request.form['editedName']
            session.add(editedItem)
            session.commit()
            return redirect(url_for('showCourses'))
    else:
        return render_template('editCourse.html',
                               courses=courses, userCourse=userCourseEdit)


# Delete a Food item
@app.route('/food/<int:foodItem_id>/delete', methods=['GET', 'POST'])
def deleteFoodItem(foodItem_id):
    if 'username' not in login_session:
            return redirect('/login')
    courses = session.query(Course).order_by(asc(Course.name))
    itemToDelete = session.query(FoodItem).filter_by(id=foodItem_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        # flash('Menu Item Successfully Deleted')
        return redirect(url_for('showCourses'))
    else:
        return render_template('deleteItem.html',
                               item=itemToDelete, courses=courses)


# Delete a Course
@app.route('/course/delete', methods=['GET', 'POST'])
def deleteCourse():
    if 'username' not in login_session:
            return redirect('/login')
    courses = session.query(Course).order_by(asc(Course.name))
    user = session.query(UserTable).filter_by(
            username=login_session['username']).one_or_none()
    userCourseDelete = session.query(Course).filter_by(user_id=user.id).all()
    if not userCourseDelete:
            flash('Cannot delete any Courses - '
                  'Can only delete courses you have created')
    if request.method == 'POST':
        if request.form['courseDelete']:
            course_id = request.form['courseDelete']
            itemToDelete = session.query(Course).filter_by(id=course_id).one()
            session.delete(itemToDelete)
            session.commit()
            # flash('Menu Item Successfully Deleted')
            return redirect(url_for('showCourses'))
    else:
        return render_template('deleteCourse.html', courses=courses,
                               userCourse=userCourseDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
