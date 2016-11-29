FROM python:3.5

ADD requirements.txt /src/requirements.txt

RUN pip install -r /src/requirements.txt

ADD handlers /src/handlers
ADD app.py /src/app.py

EXPOSE 8888

CMD ["python", "/src/app.py"]
