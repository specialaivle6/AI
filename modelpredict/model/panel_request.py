from pydantic import BaseModel
from typing import List

class PanelRequest(BaseModel):
    user_id: str
    id: int
    model_name: str
    serial_number: int
    pmp_rated_w: float
    temp_coeff: float
    annual_degradation_rate: float
    lat: float
    lon: float
    installed_at: str
    installed_angle: float
    installed_direction: str
    temp: List[float]
    humidity: List[float]
    windspeed: List[float]
    sunshine: List[float]
    actual_generation: float
