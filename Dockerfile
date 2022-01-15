FROM ubuntu:latest
LABEL maintainer="daniel@skitzen.com"

RUN apt-get update -y && apt-get install -y python-pip python-dev python

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["python"]

CMD ["api.py"]