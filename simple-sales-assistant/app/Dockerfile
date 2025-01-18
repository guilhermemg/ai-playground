FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

RUN pip install --upgrade pip

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 -y

WORKDIR /usr/src/app

COPY ./requirements.txt $WORKDIR
RUN pip install -r requirements.txt

COPY ./app/ $WORKDIR

EXPOSE 8000

CMD ["python", "app_server.py"]