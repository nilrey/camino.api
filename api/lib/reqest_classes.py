from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError


class ImageRun(BaseModel):
   name: str = Field(default="")
   weights:str = Field(default="")
   hyper_params:str = Field(default="")
   in_dir:str  = Field(default="")
   out_dir:str = Field(default="")
   network:str = Field(default="")
   ann_mode:str = Field(default="")
   yolov5s:str = Field(default="")
   host_web:str = Field(default="camino-api")
   work_time:str = Field(default="")
   

   def getAllParams(self):
    return {'name': self.name, 
            'weights': self.weights, 
            'hyper_params': self.hyper_params, 
            'in_dir': self.in_dir, 
            'out_dir': self.out_dir, 
            'network': self.network, 
            'ann_mode': self.ann_mode, 
            'yolov5s': self.yolov5s, 
            'host_web': self.host_web, 
            'work_time': self.work_time, 
            }
   

class ANNEventBeforeRun(BaseModel):
    msg: str = Field(default="")
    details: str = Field(default="")


class ContainerCreate(BaseModel):
   name: str = Field(default="")
   weights:str = Field(default="")
   hyper_params:str = Field(default="")
   in_dir:str  = Field(default="")
   out_dir:str = Field(default="")
   network:str = Field(default="")
   ann_mode:str = Field(default="")
   yolov5s:str = Field(default="")
   host_web:str = Field(default="camino-api")
   work_time:str = Field(default="")
   
   

   def getAllParams(self):
    return {'name': self.name, 
            'weights': self.weights, 
            'hyper_params': self.hyper_params, 
            'in_dir': self.in_dir, 
            'out_dir': self.out_dir, 
            'network': self.network, 
            'ann_mode': self.ann_mode, 
            'yolov5s': self.yolov5s, 
            'host_web': self.host_web, 
            'work_time': self.work_time, 
            }
   