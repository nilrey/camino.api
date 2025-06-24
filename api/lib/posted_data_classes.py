from pydantic import BaseModel, EmailStr, Field, field_validator
import datetime as dt
from typing import Optional, List

class PostedDataCreateContainer(BaseModel):
    name: Optional[str] = ""
    ann_mode: Optional[str] = ""
    weights: Optional[str] = ""
    hyper_params: Optional[str] = ""
    in_dir: Optional[str] = ""
    out_dir: Optional[str] = ""
    markups: Optional[str] = ""
    video_storage: Optional[str] = ""
    network: Optional[str] = ""
    dataset_id: Optional[str] = ""
    only_verified_chains: bool = False
    only_selected_files: List[str] = []

class PostedDataImageRun(BaseModel):
   name: str = Field(default="")
   ann_mode:str = Field(default="")
   weights:str = Field(default="")
   hyper_params:str = Field(default="")
   in_dir:str  = Field(default="")
   out_dir:str = Field(default="")
   markups:str = Field(default="")
   video_storage:str = Field(default="")
   network:str = Field(default="")
   dataset_id:str = Field(default="")
   only_verified_chains:bool = Field(default=False)
   only_selected_files: list = Field(default=[])
   

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
            'dataset_id': self.dataset_id, 
            'only_verified_chains': self.only_verified_chains, 
            'only_selected_files': self.only_selected_files
            }


class PostedDataDatasetExport(BaseModel):
   target_dir:str = Field(default="")
   only_verified_chains:bool = Field(default=False)
   only_selected_files: list = Field(default=[])

   def getAllParams(self):
      return {'target_dir': self.target_dir, 
            'only_verified_chains': self.only_verified_chains, 
            'only_selected_files': self.only_selected_files
            }
   

class PostedDataDatasetImport(BaseModel):
   files: list = Field(default=[])


class PostedDataContainerCreate(BaseModel):
   name: str = Field(default="")
   ann_mode:str = Field(default="")
   weights:str = Field(default="")
   hyper_params:str = Field(default="")
   in_dir:str  = Field(default="")
   out_dir:str = Field(default="")
   markups:str = Field(default="")
   video_storage:str = Field(default="")
   network:str = Field(default="")

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
            # 'host_web': self.host_web, 
            }


class PostedDataAnnExport(BaseModel):
   image_id:str = Field(default="") 
   weights:str = Field(default="") # path to weights file
   export:str = Field(default=f"ann_export_{int(dt.datetime.now().timestamp())}" )

class PostedDataContainerStop(BaseModel):
   dataset_id: str = Field(default="undefined")

class PostedDataVideoConverter(BaseModel):
    source_dir: str
    target_dir: str