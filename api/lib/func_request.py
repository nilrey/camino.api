from fastapi import Request

def get_request_params(req:Request):
   params = {}
   for key, par in req.query_params.items():
      params[key] = par
   for key, par in req.path_params.items():
      params[key] = par

   return (params)
