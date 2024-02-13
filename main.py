# taken from https://fastapi.tiangolo.com/tutorial/first-steps/
# for proper work install first:
# sudo apt install python3-pip
# pip install "fastapi[all]"
# sudo apt install uvicorn
# Then, try to run command from the current folder:
# uvicorn main:app --reload 

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World FasAPI "}

@app.get("/set")
async def setset():
    return {"message": "Set url"}