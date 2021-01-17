from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import scoped_session
import models
from db import local_session, engine, Base



app = Flask(__name__)
CORS(app)
app.session = scoped_session(local_session)


# TODO
# add exceptions


# client commands
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





############## app routes ##############

@app.route('/')
def greeting():
    return 'Welcome to Space!'



@app.route('/add_ship', methods=['POST'])
def add_ship():

    # check form-data
    try:
        ship_name = request.form['name']
        model = request.form['model']
        location = int(request.form['location'])
        status = request.form['status']
    except KeyError:
        print("Something wrong with form-data!")
        return jsonify(msg='Invalid form-data.'), 406
    
    if not all([ship_name, model, status]):
        return jsonify(msg="'name', 'model', 'status' cannot be null."), 406

    # assume that the frontend makes sure user enter a non-empty shipname, model, status
    # but does not check uniqueness
    test_ship = app.session.query(models.Spaceships).filter_by(name=ship_name).first()
    if test_ship:
        return jsonify(msg=f"The spaceship name '{ship_name}' has been used, please try another name."), 406
    
    test_location = app.session.query(models.Locations).filter_by(id=location).first()
    if not test_location:
        return jsonify(msg=f"The location (id: {location}) does not exists."), 404
    
    # if location exists, update 'stationed'
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
    # assume the frontend will send the ship id and status by args
    try:
        sid = request.args.get('id')
        status = request.args.get('status')
    except KeyError:
        print("Something wrong with args!")
        return jsonify(msg="Invalid arguments."), 406

    if not all([sid, status]):
        raise KeyError("Empty value received!")
        return jsonify(msg="'Spaceship id' or 'status cannot be null.")

    # check validity of status
    if not valid_status(status):
        return jsonify(msg=f"Invalid spaceship status: {status}")

    # check if the corresponding ship exists
    test_ship = app.session.query(models.Spaceships).filter_by(id=sid).first()
    if not test_ship:
        return jsonify(msg=f"The spaceship (id: {sid}) does not exist."), 404

    # if no problem with data
    return jsonify(msg=f"You successfully updated your spaceship '{test_ship.name}' status to '{status}'!")

    

@app.route('/add_location', methods=["POST"])
def add_location():
    try:
        city_name = request.form['city_name']
        planet_name = request.form['planet_name']
        capacity = request.form['capacity']
    except KeyError:
        print("Something wrong with form-data!")
        return jsonify(msg='Invalid form-data.'), 406

    # planet name and capacity cannot be empty
    if not all(['planet_name', 'capacity']):
        raise KeyError('Empty value received!')
        return jsonify(msg="'Planet name' or 'capacity' can not be null."), 406

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
        return jsonify(msg=f"Spaceship (id: {sid}) not found."), 404
    
    app.session.delete(rm_ship)
    app.session.commit()
    return jsonify(msg=f"Spaceship (id: {sid}) was successfully removed.")



@app.route('/remove_location/<int:lid>', methods=['DELETE'])
def remove_location(lid: int):
    # retireve the db model object from daatabase
    rm_location = app.session.query(models.Locations).filter_by(id=lid).first()
    # if not exist, tell the user that location is not in the system
    if not rm_location:
        return jsonify(msg=f"Location (id: {lid}) not found."), 404

    # delete the locatin from the db
    app.session.delete(rm_location)
    app.session.commit()
    return jsonify(msg=f"Location (id: {lid}) was successfully removed.")



@app.route('/travel/<int:destination>', methods=['PUT'])
def travel(destination: int):
    # assume that ship id is sent through data
    try:
        ship_id = int(request.args.get('id'))
    except KeyError:
        print("Something wrong with data!")
        return jsonify(msg="Invalid data.")


    # check if ship exists
    ship_data = app.session.query(models.Spaceships).filter_by(id=ship_id).first()
    if not ship_data:
        return jsonify(msg=f"The spaceship (id: {ship_id}) does not exist."), 404

    # check if status is right for travel
    if not ship_data.status == 'operational':
        return jsonify(msg=f"The spaceship (id: {ship_id}) is not in the status for travel."), 406


    # check if destination exists
    test_destination = app.session.query(models.Locations).filter_by(id=destination).first()
    if not test_destination:
        return jsonify(msg=f"Destination (location id: {destination}) not found."), 404
    

    # check if destination is full in capacity
    if int(test_destination.stationed) >= int(test_destination.capacity):
        return jsonify(msg=f"Destination (location id: {test_destination.id}) is currently at full capacity, cannot accomodate more spaceship."), 406

    # if not full in capacity, update 'stationed' of destination
    test_destination.stationed = test_destination.stationed + 1

    # update 'stationed' of origin
    origin = app.session.query(models.Locations).filter_by(id=ship_data.location).first()
    if origin:
        origin.stationed = origin.stationed - 1

    # update location of the ship
    app.session.query(models.Spaceships).filter_by(id=ship_id).update({"location": destination})
    app.session.commit()
    return jsonify(msg=f"You successfully travel to location (id: {destination}) with your spaceship (id: {ship_id})!")


if __name__ == "__main__":
    app.run(port=5000, debug=True)


# helper functions
def valid_status(s: str) -> bool:
    return s in ['decommissioned', 'maintenance', 'operational']