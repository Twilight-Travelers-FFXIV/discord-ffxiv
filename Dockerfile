FROM python:3.13.0b1-slim
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN apt update

CMD [ "python3", "main.py" ]