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





# app routes
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
        print("Something wrong with form data!")
        return jsonify(msg='Invalid form-data.')
    
    # assume that the frontend makes sure user enter a non-empty shipname, model, status
    # but does not check uniqueness
    test_ship = app.session.query(models.Spaceships).filter_by(name=ship_name).first()
    if test_ship:
        return jsonify(msg=f"The spaceship name '{ship_name}' has been used, please try another name."), 406
    
    test_location = app.session.query(models.Locations).filter_by(id=location).first()
    if not test_location:
        return jsonify(msg=f"No such location (id: {location})."), 406
    
    # create a spaceship object
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
    
    sid = request.args.get('id')
    status = request.args.get('status')
    
    if not all([sid, status]):
        raise KeyError(description="Empty value received!")

    # check if the corresponding ship exists
    test_ship = app.session.query(models.Spaceships).filter_by(id=sid).first()
    if not test_ship:
        return jsonify(msg="No such spaceship (id: {sid}) exists."), 404
    return jsonify(msg=f"You successfully updated your spaceship '{test_ship.name}' status to '{status}'!")

    

@app.route('/add_location', methods=["POST"])
def add_location():
    city_name = request.form['city_name']
    planet_name = request.form['planet_name']
    # assume that frontend handles empty planet name, capacity
    capacity = request.form['capacity']
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
def travel(where_start: int, destination: int):
    # assume that ship id is sent through data
    ship = request.data.get('ship_id')
    # check if destination exists
    test_location = app.session.query(models.Locations).filter_by(id=destination).first()
    if not test_location:
        return jsonify(msg=f"Location (id: {destination}) does not exist."), 406

    # update location of the ship
    app.session.query(models.Spaceships).filter_by(id=ship).update({"location": destination})
    app.session.commit()
    return jsonify(msg=f"You successfully travel to location (id: {destination}) with your spaceship (id: {ship})!")


if __name__ == "__main__":
    app.run(port=5000, debug=True)


# helper functions
def valid_status(s: str) -> bool:
    return s in ['decommissioned', 'maintenance', 'operational']