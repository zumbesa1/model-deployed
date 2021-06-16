FROM python:3.8
#FROM ubuntu:latest
COPY . /app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
#ENTRYPOINT ["python3"]
EXPOSE 8000
CMD ["python", "run.py"]