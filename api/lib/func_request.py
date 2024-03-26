from fastapi import Request

def get_request_params(req:Request, fromQS = True, fromPath = True):
    params = {}
    if fromQS:
        for key, par in req.query_params.items():
            params[key] = par
    if fromPath:
        for key, par in req.path_params.items():
            params[key] = par

    return (params)
