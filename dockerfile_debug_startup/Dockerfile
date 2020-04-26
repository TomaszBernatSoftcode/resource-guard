FROM python:3
ENV PYTHONUNBUFFERED 1
ENV DEBUG 1
ENV SECRET_KEY 4r@x#q8$2z9dto+wtk3tq+4%_fu_()+3-9s(-l6igdn0hoh3op
ENV DJANGO_SETTINGS_MODULE file_guard.settings
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/