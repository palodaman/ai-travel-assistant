from pydantic import BaseModel, Field, constr, confloat

City = constr(min_length=1, strip_whitespace=True)

class WeatherInput(BaseModel):
    city: City

class ConvertInput(BaseModel):
    amount: confloat(ge=0) = Field(..., description="Amount to convert")
    from_: constr(min_length=3, max_length=3) = Field(..., alias="from")
    to: constr(min_length=3, max_length=3)
