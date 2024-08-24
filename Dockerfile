FROM ubuntu:latest

RUN apt-get update && apt-get install -y netcat-openbsd

CMD echo "hello world" | nc server 12345