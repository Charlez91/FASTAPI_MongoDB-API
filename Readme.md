# A BASIC FASTAPI API with NoSQL db.

Make sure MongoDB is installed from official distro and start the mongodb server with
```bash
sudo service mongod start
```

create a virtual environment and activate with
```bash
python3 -m venv venv
source venv/bin/activate
```

Install all requirements with
```bash
pip install -r requirements.txt
```

Fill database with data from courses.json by running
```bash
python3 scripts.py
```

run app with reload flag
```bash
uvicorn main:app --reload
```

run tests with
```bash
pytest
```