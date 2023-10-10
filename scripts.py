""" 
Script to parse course information from courses.json, create the appropriate databases and
collection(s) on a local instance of MongoDB, create the appropriate indices (for efficient retrieval)
and finally add the course data on the collection(s). ##Run Only Once
"""
import os
import json

import pymongo
from dotenv import load_dotenv

load_dotenv()

#connect to the database based on pymongo docs
print("-> connecting to database\n\tcreating db \n creating collection")
client = pymongo.MongoClient(os.getenv('MONGODB_URI', "mongodb://localhost:27017/"))#connect to mongodb
db =  client["Courses"]#creates database
collection = db["courses"]#creates collections synonymous to tables

print("reading from courses.json")
#read courses from courses.json
with open("courses.json", "r") as f:
    courses = json.load(f)

print("inserting records into db")
#creating index for efficient retrieval
collection.create_index("name")

#add rating field to each course
for course in courses:
    course["rating"] = {'total':0, 'count':0}
    #add rating to each chapter
    for chapter in course["chapters"]:
        chapter['rating'] = {'total':0, 'count':0}
    
    #add courses to db collections(table)
    collection.insert_one(course)

print("closing db")
#close mongodb connection very important
client.close()