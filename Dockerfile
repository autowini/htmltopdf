FROM python:3.11-bookworm

WORKDIR /app
COPY . /app

# Timezone: KST 설정
RUN ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

RUN pip3 install -r requirements.txt

# Playwright: browser and OS dependencies are installed with a single command
RUN playwright install --with-deps chromium

CMD ["python3", "app.py"]
