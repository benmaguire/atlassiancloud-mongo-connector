FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y python3 python3-pip libssl-dev

COPY jira-mongosink/ /app/jira-mongosink/
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY requirements.txt /requirements.txt
RUN pip3 install --upgrade -r /requirements.txt
RUN rm /requirements.txt
RUN chmod 755 /docker-entrypoint.sh

CMD ["/docker-entrypoint.sh"]

