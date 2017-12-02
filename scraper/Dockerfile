FROM python:3.5-slim
MAINTAINER Benjamin Misell <beninjam174@gmail.com>

COPY requirements.txt /
RUN pip3 install -r requirements.txt && rm requirements.txt

COPY scraper.py /app/

CMD python3 /app/scraper.py