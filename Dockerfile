FROM --platform=linux/amd64 python:3.11.4

COPY ./src .

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "main.py"] 