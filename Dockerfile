FROM python:3.10.12

WORKDIR /usr/app/src

COPY .env main.py ./

CMD [ "python", "./main.py" ]