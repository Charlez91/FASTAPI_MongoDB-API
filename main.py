import contextlib
from typing import Any
import os

from fastapi import FastAPI, HTTPException, Query, Request, Body
from pymongo import  MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()#instantiate and app instance of fastapi
client = MongoClient(os.getenv('MONGODB_URI', "mongodb://localhost:27017/"))#connect to mongodb
db = client["Courses"]#connect to db Courses

@app.get('/courses')
def get_courses(sort_by:str = 'date', domain:str = None):
    # set the rating.total and rating.count to all the courses based on the sum of the chapters rating
    for course in db.courses.find():#find() returns all courses in the collection
        total = 0
        count = 0
        for chapter in course.get('chapters', []):
            with contextlib.suppress(KeyError):
                total += chapter['rating']['total']
                count += chapter['rating']['count']
        db.courses.update_one({'_id': course['_id']}, {'$set':{'rating':{'total':total, 'count':count}}})
    
    #set sort parameters by date as passed in as query params
    if sort_by == 'date':
        sort_field = 'date'
        sort_order = -1
    elif sort_by == 'rating':# sort by rating in descending order
        sort_field = 'rating.total'
        sort_order = -1
    else:#if no query param sort by default with names in ascending order
        sort_field = 'name'
        sort_order = 1
    
    query = {}
    if domain:
        query['domain'] = domain#if domain is passed in to return only courses with specified domains

    #perform db query with parameters in 1 returned
    try:
        courses = db.courses.find(query, {'_id':0, 'name':1, 'date':1, 'description':1, 'domain':1, 'rating':1}).sort(sort_field, sort_order)
    except TypeError:
        raise HTTPException(404, "No Course with stated domain found")
    return list(courses)


@app.get('/courses/{course_id}')
def get_course(course_id:str):
    #return first query with id stated
    course = db.courses.find_one({'_id': ObjectId(course_id)}, {'_id':0, 'courses':0})
    if not course:
        raise HTTPException(status_code=404, detail='Course with id not found')

        
    try:
        #set course rating to total ratings
        course['rating'] = course['rating']['total']#correct algorithm is set rating to avg ie total/count
    except KeyError:
        course['rating'] = "Course Not Rated Yet"
    
    return course


@app.get('/courses/{course_id}/{chapter_id}')
async def get_chapter(course_id:str, chapter_id:str):
    course = db.courses.find_one({'_id':ObjectId(course_id)}, {'_id':0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    chapters = course.get("chapters", [])#get chapters field and return an empty list if it doesnt exist

    try:
        #using index of chapter to get specific chapter
        chapter = chapters[int(chapter_id)]#
    except (ValueError, IndexError) as e:
        raise HTTPException(404, "Chapter not found") from e
    
    return chapter


@app.post('/courses/{course_id}/{chapter_id}')
def rate_chapters(course_id:str, chapter_id:str, rating:int = Query( ..., gt=-2, lt=2)):
    course = db.courses.find_one({'_id':ObjectId(course_id)}, {'_id':0})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if type(rating) != int:
        raise HTTPException(422, 'INVALID RATING TYPE, must be an integer')
    
    chapters = course.get("chapters", [])#get chapters field and return an empty list if it doesnt exist
    try:
        #using index of chapter to get specific chapter
        chapter = chapters[int(chapter_id)]
        #set ratings for specified chapter. total and count
        chapter['rating']['total'] += rating
        chapter['rating']['count'] += 1
    except (ValueError, IndexError) as e:
        #for chapter chapterid not int and index out of range errors
        raise HTTPException(404, "Chapter not found") from e
    except KeyError:
        #if rating or total or count doesnt exist set total to current rating
        chapter['rating'] = {'total': rating, 'count': 1}
    
    try:
        total = course['rating']['total']+rating
        count = course['rating']['total']+1
    except:
        course['rating'] = {'total':rating, 'count':1}
    
    #update db record with provided rating
    db.courses.update_one({'_id': ObjectId(course_id)}, {'$set': {'chapters': chapters, 'rating': {'total': total, 'count': count}}})
    return chapter

@app.post("/test")
async def get_params(request : Request ):
    try:
        json_body = await request.json()#body as json.. it can fail if body is not json
    except:
        json_body = "Body Not Json so couldnt decode"
    body = await request.body()#body parsed could be from forms, multipart enc etc
    header = request.headers.items()#header of request: content type, key/token, etc
    query = request.query_params.items()#get query parameters from url string

    context = {'json_body': json_body, "body": body, "header" : header, "query_params": query}
    return context

@app.post("/bodytest")
async def get_bodyparams(body : Any = Body(...)):
    return await body

    

