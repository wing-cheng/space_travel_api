/*
    Assumptions:
        'city' can be null as a 'location' entity can mean an entire planet
        'capacity' is the max number of spaceships a 'location' can accommodate
        'capacity' >= 0, as a 'location' can station no spaceship
        'stationed' is the number of spaceships that are currently at each 'location'
*/
CREATE TABLE Locations (
    id          integer PRIMARY KEY,
    city        text,
    planet      text NOT NULL,
    capacity    integer NOT NULL,
    CHECK (capacity >= 0),
    stationed   integer NOT NULL,
    CHECK (stationed >= 0 and stationed <= capacity)
);


/*
    Assumptions:
        'name' cannot be null and must be unique
        'location' refers to an entity in 'Locations' table
        'status' can be only be the 3 given values
*/
CREATE TABLE Spaceships (
    id       integer PRIMARY KEY,
    name     text UNIQUE,
    model    text NOT NULL,
    location integer NOT NULL
    FOREIGN KEY (location) REFERENCES Locations (id),
    status   varchar(20),
    CONSTRAINT valid_status CHECK (status in ('maintenance', 'operational', 'discommissioned'))
);


