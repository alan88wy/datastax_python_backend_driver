import re
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from flask import Flask, json, jsonify, request
from flask_marshmallow import Marshmallow

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
import uuid
import os

from flask_mail import Mail, Message

app = Flask(__name__)

cloud_config= {
        'secure_connect_bundle': 'secure-connect-awcrm.zip'
}

CLIENT_ID=os.environ['CLIENT_ID'] 
CLIENT_SECRET = os.environ['CLIENT_SECRET']
JWT_SECRET = os.environ['JWT_SECRET']

app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']   # d41680001cbbea
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']   # 9dd173b4838070
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect('awcrm') # Connect to Keyspace

ma = Marshmallow(app)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = JWT_SECRET  # Change this!
jwt = JWTManager(app)
mail = Mail(app)

def checkInt(str):
    if str[0] in ('-', '+'):
        return str[1:].isdigit()
    return str.isdigit()

@app.route('/')
def hello_world():
    return '<h1>Hello World</h1>', 200


@app.route('/json')
def hello_json():
    return jsonify(message = 'Hello Json'), 200

@app.route('/not_found')
def not_found():
	return jsonify(message='Resource Not Found'), 404

@app.route('/parameters')
def parameters():
	name = request.args.get('name')
	age = request.args.get('age')

	if checkInt(age):
		age = int(age)
	else:
		return jsonify(message = "Sorry " + name + ", age enter is invalid !"), 401

	if age < 18:
		return jsonify(message="Sorry " + name + ", you are not old enough"), 401
	else:
		return jsonify(message="Welcome " + name + ", you are old enough")

@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):

	if age < 18:
		return jsonify(message="Sorry " + name + ", you are not old enough"), 401
	else:
		return jsonify(message="Welcome " + name + ", you are old enough")	

@app.route('/planets', methods=['GET'])
def planets():
	planets_list = session.execute("SELECT * FROM planet")

	return jsonify(planets_list.current_rows)

@app.route('/register', methods=['POST'])
def register():
	email = request.form['email']

	stmt = session.prepare("SELECT * FROM Users WHERE email = ? LIMIT 1")
	result = session.execute(stmt, [email])

	if (len(result.current_rows) > 0):
		return jsonify(message='That email already exists.'), 404
	else:
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		password = request.form['password']
		id = uuid.uuid1()

		session.execute("INSERT INTO Users (id, first_name, last_name, email, password) VALUES (%s,%s,%s,%s, %s)", [id, first_name, last_name, email, password])

		return jsonify(message='User created successfully'), 201

# Create a route to authenticate your users and return JWTs. The
# create_access_token() function is used to actually generate the JWT.
@app.route("/login", methods=["POST"])
def login():
	if request.is_json:
		email = request.json['email']
		password = request.json["password"]
    
	else:
		email = request.form['email']
		password = request.form['password']

	result = session.execute("SELECT * FROM users WHERE email = %(email)s", {'email':email}).one()
	
	if (str(result.password) == str(password)):
		access_token = create_access_token(identity=email)
		return jsonify(message='Login Successful!', access_token=access_token)
	else:
		return jsonify(message='Wrong password enter'), 401

@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):

	result = session.execute("SELECT * FROM users WHERE email = %(email)s", {'email':email}).one()

	if result:
		msg = Message('Your planetary API password is ' + user.password, sender='admin@planetary-api.com', recipients=['email'])
		mail.send(msg)
		return jsonify(message="Password sent to " + email)
	else:
		return jsonify(message = "That email does not exist!"), 401

@app.route('/update_user', methods=['PUT'])
@jwt_required()  
def update_user():
	email = request.form['email']
	result = session.execute("SELECT * FROM users WHERE email = %(email)s", {'email':email}).one()

	if result:
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		password = request.form['password']

		prepared = session.prepare('UPDATE users SET first_name = ?, last_name = ?, password = ? WHERE id = ?')
		session.execute(prepared, [first_name, last_name, password, user.id])
		
		return jsonify(message='You have updated user '+ first_name), 202
	else:
		return jsonify(message='That user does not exist !'), 404

@app.route('/planet_details/<string:planet_id>', methods=['GET'])
def planet_details(planet_id:str):

	id = uuid.UUID(planet_id)
	planet = session.execute("SELECT * FROM planet WHERE planet_id = %(planet_id)s", {'planet_id':id}).one()

	if planet:
		return jsonify(planet)
	else:
		return jsonify(message='That planet does not exist'), 404

@app.route('/add_planet', methods=['POST'])
@jwt_required()    # Require login using JWT before doing this add_planet
def add_planet():
	planet_name = request.form['planet_name']

	planet = session.execute("SELECT * FROM planet WHERE planet_name = %(planet_name)s", {'planet_name':planet_name}).one()

	if planet:
		return jsonify('There is already a planet by that name'), 409
	else:
		planet_id = uuid.uuid1()
		planet_type = request.form['planet_type']
		home_star = request.form['home_star']
		mass = float(request.form['mass'])
		radius = float(request.form['radius'])
		distance = float(request.form['distance'])

		session.execute("INSERT INTO planet (planet_id, planet_name, planet_type, home_star, mass, radius, distance) VALUES (%s,%s,%s,%s,%s,%s,%s)", [planet_id, planet_name, planet_type, home_star, mass, radius, distance])

		return jsonify(message='You have added a planet'), 201

@app.route('/update_planet', methods=['PUT'])
@jwt_required()  
def update_planet():
	planet_id = request.form['planet_id']
	id = uuid.UUID(planet_id)
	planet = session.execute("SELECT * FROM planet WHERE planet_id = %(planet_id)s", {'planet_id':id}).one()

	if planet:
		planet_name = request.form['planet_name']
		planet_type = request.form['planet_type']
		home_star = request.form['home_star']
		mass = float(request.form['mass'])
		radius = float(request.form['radius'])
		distance = float(request.form['distance'])

		prepared = session.prepare('UPDATE planet SET planet_name = ?, planet_type = ?, home_star = ?, mass = ?, radius = ?, distance = ? WHERE planet_id = ?')
		session.execute(prepared, [planet_name, planet_type, home_star, mass, radius, distance, planet_id])

		return jsonify(message='You have updated planet '+ planet_name), 202
	else:
		return jsonify(message='That planet does not exist !'), 404

@app.route('/delete_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()  
def delete_planet(planet_id:int):

	planet_id = request.form['planet_id']

	id = uuid.UUID(planet_id)

	planet = session.execute("SELECT * FROM planet WHERE planet_id = %(planet_id)s", {'planet_id':id}).one()

	if planet:	
		prepared = session.prepare("DELETE FROM planet WHERE planet_id = ?")
		session.execute(prepared, [planet_id])

		return jsonify(message='You have deleted planet ' + planet.planet_name), 202
	else:
		return jsonify(message='That planet does not exist !'), 404

if __name__ == '__main__':
    app.run()
