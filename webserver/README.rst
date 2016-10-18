=========
Webserver
=========

This is a webserver that can be put in front of the sesam-node in order to ensure that users
can only see the information that they are allowed to see.

Assumptions:

1. The webserver is being accessed via a frontendserver (for instance Apache or nginx) that supports
   authentication and sets the "X-Remote-User" request header.

   The webserver reads the "X-Remote-User" request header and uses the resulting value to do a search in nginx
   for the entries that the user is allowed to see.

2. Elasticsearch must be running on the address "localhost:9200". The easiest way to do that is to start
   elasticsearch in a dockercontainer with this command::

      docker run -d --name sesam-jira-currenttime-elasticsearch -p 9200:9200 -d elasticsearch




Running the pre-built Docker image
----------------------------------

::

  docker run --rm --name sesam-jira-currenttime-webserver --link=sesam-jira-currenttime-elasticsearch -p 8080:8080 knutj42/sesam-jira-currenttime-webserver



Running locally in a virtual environment
----------------------------------------

::

  cd sesam-jira-currenttime-example/webserver/webserver
  virtualenv --python=python3 venv
  . venv/bin/activate
  pip install -r requirements.txt

  python webserver.py
   * Running on http://127.0.0.1:8080/ (Press CTRL+C to quit)


The service listens on port 8080 on localhost.

Building and running in Docker
------------------------------

::

  cd sesam-jira-currenttime-example/webserver
  docker build -t sesam-jira-currenttime-webserver .
  docker run -d --name sesam-jira-currenttime-webserver --link= -p 8080:8080 sesam-jira-currenttime-webserver

