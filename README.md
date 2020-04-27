# Resource guard

Project helps to secure resources for system users. 
Data is stored for 24 hours after this time secured 
resource is deleted from db if it was url or from persistent storage directory (for this implementation I've used dropbox). 

## Getting Started

These instructions provide clarification on contribution for project process. It is also helpful 
if you want to just play around with project.

### Prerequisites

1. For usage of containerized version of application you have to download and run DOCKER 3rd part (available on Win Pro, Mac, Linux OSes)
2. Project requires usage of PostgreSQL version 12 (for more information check https://www.postgresql.org/download/)

### Running application

1. Locally:
* Create your local db in pgAdmin or via psql command.
* Set environemnt vairables necessary for project:
```
    // postgres db connection credentails
    POSTGRES_DB_NAME='postgres'
    POSTGRES_DB_USER='postgres'
    POSTGRES_DB_PASSWORD='postgres'
    POSTGRES_DB_HOST='localhost'
    POSTGRES_DB_PORT='5432'
    
    // addionals env config
    DEBUG=1
```
* Download this project via download button or git clone command.
* Install python 3.8 (for more infor check https://www.python.org/downloads/)
* In the main directory of cloned repository create virtualenvironment (https://docs.python.org/3/library/venv.html)
* Run your virtual environment 
* Run command: ```pip install -r requirements.txt``` (if you have problem with ```psycopg2``` please install binary version )
* Run command: ```python manage.py migrate```
* Run command: ```python manage.py createsuperuser --no-input```
* Run command: ```python manage.py runserver```
* Go to ```localhost:8000```
* Log in with default credentials for admin:
```
        login: admin
        password: admin
```
* After login you will be redirected to index page. Admin panel is accessible only for admin users under ```localhost:8000/admin```

You are now ready to go. You can start testing application. Files will be stored on your local machine.


2. With docker:
* Download this project via download button or git clone command.
* Go to directory where project lives and run:
```
        docker-compose up -d
```
* Wait for a container to build and go to ```localhost:8000```
* Log in with default credentials for admin:
```
        login: admin
        password: admin
```

## Running the tests

1. When running locally:
* Go to directory where project lives and run your virtualenvironment.
* Run command ```python manage.py test guard_engine.tests.integration```
2. When running via docker containters:
* Spin up your web container
* Attach to its interactive mode (```docker exec -it <container name> /bin/bash```) 
and run ```python manage.py test guard_engine.tests.integration```

## Deployment

Application is deployed via heroku on https://resource-guard.herokuapp.com/ . 
It uses Heroku's postgres free db and dropbox persistent storage for file management. 
Contact me if u want to take part in testing process. 

## Authors

* **Tomasz Bernat**

## License

This project is licensed under the MIT License