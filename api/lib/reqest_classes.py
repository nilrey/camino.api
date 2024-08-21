from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError


class ImageRun(BaseModel):
   name: str = Field(default="")
   weights:str = Field(default="")
   hyper_params:str = Field(default="")
   in_dir:str  = Field(default="/home/ubuntu/Documents/images/bytetracker/000/input")
   out_dir:str = Field(default="/home/ubuntu/Documents/images/bytetracker/000/output")

   def getAllParams(self):
    return {'name': self.name, 
            'weights': self.weights, 
            'hyper_params': self.hyper_params, 
            'in_dir': self.in_dir, 
            'out_dir': self.out_dir, 
            }
   

class ANNEventBeforeRun(BaseModel):
    msg: str = Field(default="")
    details: str = Field(default="")