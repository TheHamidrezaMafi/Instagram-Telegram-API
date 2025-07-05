
# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi
# import pymongo
# uri = "mongodb+srv://hmafi72:ASjeTbaPUuJXRL4L@cluster0.lcomdtc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# # Create a new client and connect to the server
# client = MongoClient(uri, server_api=ServerApi('1'))
# mydb = client["test"]
# client.drop_database
# print(client.list_database_names())

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the PyMongo tutorial!"}
