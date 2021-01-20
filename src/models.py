from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from db import Base, engine


# database model definitions 
class Locations(Base):
    __tablename__ = 'locations'

    # columns
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=True)
    planet = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    stationed = Column(Integer, nullable=False)

    # check statements
    CheckConstraint('capacity>=0', name='check_capacity')
    CheckConstraint('stationed>=stationed', name='check_stationed')
    CheckConstraint('capacity>=stationed', name='check_capacity_stationed')



class Spaceships(Base):
    __tablename__ = 'spaceships'

    # columns
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    model = Column(String, nullable=False)
    # location can be null as location can be removed
    location = Column(Integer, ForeignKey("locations.id"), nullable=False)
    status = Column(String, nullable=False)

    # relationships
    where = relationship("Locations", backref='spaceships')
