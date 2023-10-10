from fastapi.testclient import TestClient
from pymongo import MongoClient
from bson import ObjectId
import pytest

from main import app


client = TestClient(app)
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['Courses']

#test the Get Courses endpoint that returns all courses in db
def test_get_courses_no_params():
    response = client.get("/courses")
    courses = response.json()
    courses_fromdb = db.courses.find({}, {'_id':0, 'name':1, 'date':1, 'description':1, 'domain':1, 'rating':1}).sort('date', -1)
    assert len(courses) > 0
    assert response.status_code == 200
    assert courses == list(courses_fromdb)

def test_get_courses_sort_by_alphabetical():
    response = client.get("/courses?sort_by=alphabetical")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert sorted(courses, key=lambda x: x['name']) == courses
     

def test_get_courses_sort_by_date():
    response = client.get("/courses?sort_by=date")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert sorted(courses, key=lambda x: x['date'], reverse=True) == courses

def test_get_courses_sort_by_rating():
    response = client.get("/courses?sort_by=rating")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert sorted(courses, key=lambda x: x['rating']['total'], reverse=True) == courses

def test_get_courses_filter_by_domain():
    response = client.get("/courses?domain=mathematics")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert all([c['domain'][0] == 'mathematics' for c in courses])

def test_get_courses_filter_by_nonexistent_domain():
    response = client.get("/courses?domain=pets")
    assert response.status_code == 200
    assert response.json() == []
    
def test_get_courses_filter_by_domain_and_sort_by_alphabetical():
    response = client.get("/courses?domain=mathematics&sort_by=alphabetical")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert all([c['domain'][0] == 'mathematics' for c in courses])
    assert sorted(courses, key=lambda x: x['name']) == courses
    
def test_get_courses_filter_by_domain_and_sort_by_date():
    response = client.get("/courses?domain=mathematics&sort_by=date")
    assert response.status_code == 200
    courses = response.json()
    assert len(courses) > 0
    assert all([c['domain'][0] == 'mathematics' for c in courses])
    assert sorted(courses, key=lambda x: x['date'], reverse=True) == courses


#testing course details
def test_get_course_by_id_exists():
    id = "651c4ce29f65047e5a9e3ff5"
    response = client.get(f"/courses/{id}")
    assert response.status_code == 200
    course = response.json()
    # get the course from the database
    course_db = db.courses.find_one({'_id': ObjectId(f'{id}')})
    # get the name of the course from the database
    name_db = course_db['name']
    # get the name of the course from the response
    name_response = course['name']
    # compare the two
    assert name_db == name_response
     
     
def test_get_course_by_id_not_exists():
    response = client.get("/courses/6431137ab5da949e5978a280")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Course with id not found'}


def test_get_chapter_info():
    id = "651c4ce29f65047e5a9e3ff5"
    response = client.get(f"/courses/{id}/1")
    assert response.status_code == 200
    chapter = response.json()
    assert chapter['name'] == 'Big Picture of Calculus'
    assert chapter['text'] == 'Highlights of Calculus'
    
    
def test_get_chapter_info_not_exists():
    id = "651c4ce29f65047e5a9e3ff5"
    response = client.get(f"/courses/{id}/990")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Chapter not found'}


def test_get_chapter_course_not_exists():
    response = client.get("/courses/6431137ab5da949e5978a281/1")
    assert response.status_code == 404
    assert response.json() == {'detail': "Course not found"}

def test_rate_chapter():
    course_id = "651c4ce29f65047e5a9e3ff5"
    chapter_id = "1"
    rating = 1

    response = client.post(f"/courses/{course_id}/{chapter_id}?rating={rating}")

    assert response.status_code == 200

    # Check if the response body has the expected structure
    assert "name" in response.json()
    assert "rating" in response.json()
    assert "total" in response.json()["rating"]
    assert "count" in response.json()["rating"]

    assert response.json()["rating"]["total"] > 0
    assert response.json()["rating"]["count"] > 0
     
def test_rate_chapter_not_exists():
    response = client.post("/courses/6431137ab5da949e5978a281/990/rate", json={"rating": 1})
    assert response.status_code == 404
    assert response.json() == {'detail': 'Not Found'}

def test_rate_chapter_with_invalid_rating():
    course_id = "651c4ce29f65047e5a9e3ff5"
    chapter_id = "1"
    rating = 2#rating can only be 1 or -1

    response = client.post(f"/courses/{course_id}/{chapter_id}?rating={rating}")

    assert response.status_code == 422

    