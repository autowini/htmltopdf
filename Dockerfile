FROM python:3.12-slim-bookworm

COPY . /app
WORKDIR /app

RUN apt-get update # && apt-get install -y apt-transport-https
RUN apt-get -y install wkhtmltopdf

RUN pip3 install -r requirements.txt
CMD ["python3", "api.py"]

