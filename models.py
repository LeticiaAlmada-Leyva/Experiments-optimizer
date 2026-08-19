from sqlalchemy import Column, Integer, String, Float
from database import Base

class Experiments(Base):
    __tablename__ = "Experiments"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identification
    doi = Column(String, index=True, nullable=False)
    microalgae_precursor = Column(String, nullable=False)
    
    # Independent Variables (Inputs)
    temperature_c = Column(Float, nullable=True)        # °C
    time_h = Column(Float, nullable=True)               # h
    weight_vol_ratio = Column(String, nullable=True)    # Can handle texts, ranges like "2% - 10% p/v"
    solvent = Column(String, nullable=True, default="water")
    pretreatment = Column(String, nullable=True)        # Dried mass, biomass, etc.
    
    # Dependent Variables (Outputs / Results)
    yield_pct = Column(Float, nullable=True)            # %
    size_nm = Column(Float, nullable=True)              # nm
    qy_pct = Column(Float, nullable=True)               # % (Quantum Yield)
    lambda_exc_nm = Column(Float, nullable=True)        # nm
    lambda_em_nm = Column(Float, nullable=True)         # nm