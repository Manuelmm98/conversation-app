# syntax=docker/dockerfile:1

FROM python:3.10.6-slim-bullseye
RUN apt update && \
  apt upgrade -y && \
  apt install -y git && \
  apt install -y ffmpeg
WORKDIR /webapi
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_DEBUG 1
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0" ]
