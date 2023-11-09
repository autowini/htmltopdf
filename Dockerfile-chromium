FROM python:3.11-bookworm

WORKDIR /app
COPY . /app

RUN apt-get update

RUN pip3 install -r requirements.txt

RUN playwright install --with-deps chromium

CMD ["python3", "app.py"]
