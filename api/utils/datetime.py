from datetime import datetime

def get_dt_now_noms()->str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_dt_now_noms_nows()->str:
    return datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

def get_dt_now()->str:
    return str(datetime.now())