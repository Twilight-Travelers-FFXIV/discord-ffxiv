FROM python:3.12.0rc2-slim
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN apt update

CMD [ "python3", "main.py" ]