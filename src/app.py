from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import scoped_session
import models
from db import local_session, engine, Base



app = Flask(__name__)
CORS(app)
app.session = scoped_session(local_session)




############ client commands ##########
@app.cli.command('db_create')
def db_create():
    Base.metadata.create_all(bind=engine)
    print("Database Created!")


@app.cli.command('db_drop')
def db_drop():
    app.session.close()
    Base.metadata.drop_all(bind=engine)
    print("Database Dropped!")


@app.cli.command('db_seed')
def db_seed():
    earth = models.Locations(
        city = 'Sydney',
        planet = 'Earth',
        capacity = 50,
        stationed = 0,
    )
    app.session.add(earth)
    app.session.commit()
    print("Database seeded!")




############ helper functions ############

def valid_status(s: str) -> bool:
    return s in ['decommissioned', 'maintenance', 'operational']




############## app routes ##############

@app.route('/')
def greeting():
    return 'Welcome to Space!'



@app.route('/add_ship', methods=['POST'])
def add_ship():

    # assume that frontend only receive int for 'location'
    try:
        ship_name = request.form['name']
        model = request.form['model']
        location = int(request.form['location'])
        status = request.form['status']
    except (KeyError, ValueError):
        print("Something wrong with form-data!")
        return jsonify(msg='Invalid form-data.'), 406


    if not all([ship_name, model, status, location]):
        return jsonify(msg="'name', 'model', 'status', 'location' cannot be null."), 406

    # assume that the frontend makes sure user enter a non-empty shipname, model, status
    # but does not check uniqueness
    test_ship = app.session.query(models.Spaceships).filter_by(name=ship_name).first()
    if test_ship:
        return jsonify(msg=f"The spaceship name '{ship_name}' has been used, please try another name."), 406
    
    test_location = app.session.query(models.Locations).filter_by(id=location).first()
    if not test_location:
        return jsonify(msg=f"Location with id: {location} does not exists."), 404
    
    # check if the capacity of 'location' is full
    if int(test_location.stationed) >= int(test_location.capacity):
        return jsonify(msg=f"Location (id: {location}) is full in capacity, please choose another location for your spaceship."), 403

    # update 'stationed'
    test_location.stationed = int(test_location.stationed) + 1

    # if no problem with the data, create a spaceship object
    new = models.Spaceships(
        name=ship_name,
        model=model,
        location=location,
        status=status
    )
    app.session.add(new)
    app.session.commit()
    ok_str = f"New spaceship (id: {new.id}) added!"
    print(ok_str)
    return jsonify(msg=ok_str)



@app.route('/update_ship_status', methods=['PUT'])
def update_ship_status():
    # assume that Front-end sends the parameters to back-end through arguments
    try:
        sid = int(request.args.get('id'))
        status = request.args.get('status')
    except (KeyError, ValueError):
        print("Something wrong with args!")
        return jsonify(msg="Invalid arguments."), 406

    if not all([sid, status]):
        return jsonify(msg="'Spaceship id' or 'status cannot be null."), 406

    # check validity of status
    if not valid_status(status):
        return jsonify(msg=f"Invalid spaceship status: {status}"), 406

    # check if the corresponding ship exists
    test_ship = app.session.query(models.Spaceships).filter_by(id=sid).first()
    if not test_ship:
        return jsonify(msg=f"Spaceship with id: {sid} does not exist."), 404

    if test_ship.status == status:
        return jsonify(msg=f"Spaceship (id: {sid}) is already in status '{status}'"), 406

    # update the status
    test_ship.status = status
    app.session.commit()

    # if no problem with data
    return jsonify(msg=f"You successfully updated your spaceship '{test_ship.name}' status to '{status}'!")

    

@app.route('/add_location', methods=["POST"])
def add_location():
    # assume that Front-end will not accept any empty value for the parameters
    try:
        city_name = request.form['city_name']
        planet_name = request.form['planet_name']
        capacity = int(request.form['capacity'])
    except (KeyError, ValueError):
        print("Something wrong with form-data!")
        return jsonify(msg='Invalid form-data.'), 406

    # planet name and capacity cannot be empty
    if not all(['planet_name', 'capacity']):
        return jsonify(msg="'planet_406name' or 'capacity' can not be null."), 406

    # check if there already exists planet with the same planet and city name
    test_same_name = app.session.query(models.Locations).filter_by(city=city_name, planet=planet_name).first()
    if test_same_name:
        return jsonify(msg=f"Location '{planet_name} {city_name}' already exists, please register with another name"), 406

    new = models.Locations(
        city = city_name,
        planet = planet_name,
        capacity = capacity,
        stationed = 0
    )
    app.session.add(new)
    app.session.commit()
    return jsonify(msg="Location successfully added!")



@app.route('/remove_ship/<int:sid>', methods=['DELETE'])
def remove_ship(sid: int):
    # retreive the db model object from database
    rm_ship = app.session.query(models.Spaceships).filter_by(id=sid).first()
    # if not exist, tell the user that ship not in the system
    if not rm_ship:
        return jsonify(msg=f"Spaceship with id: {sid} not found."), 404
    
    # decrease 'stationed' of the location at which the spaceship is at
    rm_ship.where.stationed = rm_ship.where.stationed - 1

    app.session.delete(rm_ship)
    app.session.commit()
    return jsonify(msg=f"Spaceship (id: {sid}) was successfully removed.")



@app.route('/remove_location/<int:lid>', methods=['DELETE'])
def remove_location(lid: int):

    # retireve the db model object from daatabase
    rm_location = app.session.query(models.Locations).filter_by(id=lid).first()
    # if not exist, tell the user that location is not in the system
    if not rm_location:
        return jsonify(msg=f"Location with id: {lid} not found."), 404

    # cannot remove the location if there is a spaceship
    if rm_location.stationed != 0:
        return jsonify(msg=f"Spaceships present, location (id: {lid}) cannot be removed."), 403

    # delete the locatin from the db
    app.session.delete(rm_location)
    app.session.commit()
    return jsonify(msg=f"Location (id: {lid}) was successfully removed.")



@app.route('/travel/<int:destination>', methods=['PUT'])
def travel(destination: int):
    # assume that ship_id is sent through arguements
    # assume that front-end only accepts integer for ship_id
    try:
        ship_id = int(request.args.get('id'))
    except (KeyError, ValueError):
        print("Something wrong with data!")
        return jsonify(msg="Invalid data."), 406


    # check if ship exists
    ship_data = app.session.query(models.Spaceships).filter_by(id=ship_id).first()
    if not ship_data:
        return jsonify(msg=f"Spaceship with id: {ship_id} does not exist."), 404

    # check if status is right for travel
    if ship_data.status != 'operational':
        return jsonify(msg=f"Spaceship (id: {ship_id}) is not in the status for travel."), 403

    # if the spaceship is already at the destination
    if ship_data.location == destination:
        return jsonify(msg=f"Spaceship (id: {ship_id}) is already at destination (id: {destination})."), 406

    # check if destination exists
    test_destination = app.session.query(models.Locations).filter_by(id=destination).first()
    if not test_destination:
        return jsonify(msg=f"Destination (location id: {destination}) not found."), 404
    

    # check if destination is full in capacity
    if int(test_destination.stationed) >= int(test_destination.capacity):
        return jsonify(msg=f"Destination (location id: {test_destination.id}) is currently at full capacity, cannot accomodate more spaceship."), 403

    # if not full in capacity, update 'stationed' of destination
    test_destination.stationed = test_destination.stationed + 1

    # update 'stationed' of origin
    origin = app.session.query(models.Locations).filter_by(id=ship_data.location).first()
    if origin:
        origin.stationed = origin.stationed - 1

    # update location of the ship
    ship_data.location = destination
    app.session.commit()
    return jsonify(msg=f"Spaceship (id: {ship_id}) traveled to location (id: {destination}) successfully!")


if __name__ == "__main__":
    app.run(port=5000, debug=True, host='0.0.0.0')