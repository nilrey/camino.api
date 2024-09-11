from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError
import datetime as dt

class ImageRun(BaseModel):
   name: str = Field(default="")
   ann_mode:str = Field(default="")
   weights:str = Field(default="")
   hyper_params:str = Field(default="")
   in_dir:str  = Field(default="")
   out_dir:str = Field(default="")
   video_storage:str = Field(default="")
   network:str = Field(default="")
   host_web:str = Field(default="")
   

   def getAllParams(self):
    return {'name': self.name, 
            'ann_mode': self.ann_mode, 
            'weights': self.weights, 
            'hyper_params': self.hyper_params, 
            'in_dir': self.in_dir, 
            'out_dir': self.out_dir, 
            'video_storage': self.video_storage, 
            'network': self.network, 
            'host_web': self.host_web, 
            }
   

class ANNEventBeforeRun(BaseModel):
    msg: str = Field(default="")
    details: str = Field(default="")


class ContainerCreate(BaseModel):
   name: str = Field(default="")
   ann_mode:str = Field(default="")
   weights:str = Field(default="")
   hyper_params:str = Field(default="")
   in_dir:str  = Field(default="")
   out_dir:str = Field(default="")
   markups:str = Field(default="")
   video_storage:str = Field(default="")
   network:str = Field(default="")
   host_web:str = Field(default="")

   def getAllParams(self):
    return {'name': self.name, 
            'ann_mode': self.ann_mode, 
            'weights': self.weights, 
            'hyper_params': self.hyper_params, 
            'in_dir': self.in_dir, 
            'out_dir': self.out_dir, 
            'markups': self.markups, 
            'video_storage': self.video_storage, 
            'network': self.network, 
            'host_web': self.host_web, 
            }


class ANNExport(BaseModel):
   image_id:str = Field(default="") 
   weights:str = Field(default="") # path to weights file
   export:str = Field(default=f"ann_export_{int(dt.datetime.now().timestamp())}" )