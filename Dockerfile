FROM ubuntu:latest
LABEL maintainer="daniel@skitzen.com"

RUN apt-get update -y && apt-get install -y python3-pip python3-dev python3

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["python3"]

CMD ["api.py"]