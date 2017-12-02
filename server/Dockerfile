FROM python:3.5-slim
MAINTAINER Benjamin Misell <beninjam174@gmail.com>

COPY requirements.txt /
RUN pip3 install -r requirements.txt && rm requirements.txt

COPY ./src/* /app/
EXPOSE 80
WORKDIR /app/
CMD /app/start.sh