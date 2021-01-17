from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db import Base, engine


# database model definitions 
class Locations(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=True)
    planet = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    stationed = Column(Integer, nullable=False)


class Spaceships(Base):
    __tablename__ = 'spaceships'

    # volumns
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    model = Column(String, nullable=False)
    location = Column(Integer, ForeignKey("locations.id"), nullable=True)
    status = Column(String)

    # relationships
    where = relationship("Locations", backref='spaceships')

