from pydantic import BaseModel
from typing import Optional

# Common base schema with all attributes
class ExperimentBase(BaseModel):
    doi: str
    microalgae_precursor: str
    temperature_c: Optional[float] = None
    time_h: Optional[float] = None
    weight_vol_ratio: Optional[str] = "N/A"  # Updated to str to support texts, ranges, and percentages
    solvent: Optional[str] = "water"
    pretreatment: Optional[str] = None
    yield_pct: Optional[float] = None
    size_nm: Optional[float] = None
    qy_pct: Optional[float] = None
    lambda_exc_nm: Optional[float] = None
    lambda_em_nm: Optional[float] = None

# Schema for creating records (POST)
class ExperimentCreate(ExperimentBase):
    pass

# Schema for reading/returning records (GET)
class ExperimentResponse(ExperimentBase):
    id: int

    class Config:
        from_attributes = True