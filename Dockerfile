FROM python:3.9-slim

RUN pip install syslog2irc==0.11

COPY ./config.toml .

EXPOSE 514

CMD ["syslog2irc", "config.toml"]
