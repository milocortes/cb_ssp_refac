import sqlalchemy as db
from cb_orm_model import TxTable,inen_air_pollution_cost_factors
from sqlalchemy.orm import sessionmaker 

# Create a SQLAlchemy engine 
engine = db.create_engine("sqlite:///cb_data.db")
  
# Create a SQLAlchemy session 
Session = sessionmaker(bind=engine) 
session = Session() 


row = session.execute(db.select(inen_air_pollution_cost_factors)).first()

