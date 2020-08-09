FROM pcic/geospatial-python

MAINTAINER Andrew Beveridge "andrew@beveridge.uk"

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

RUN apt update; apt install -y curl

COPY . /app

ENV PORT 80
EXPOSE 80

ENTRYPOINT [ "python3" ]

CMD [ "run_server.py" ]
