=========
Webserver
=========

This is a webserver that can be put in front of the sesam-node in order to ensure that users
can only see the information that they are allowed to see.

Assumptions: The webserver is being accessed via a frontendserver (for instance Apache or nginx) that supports
authentication and sets the "X-Remote-User" request header.

The webserver reads the "X-Remote-User" request header and uses the resulting value to do a search in nginx
for the entries that the user is allowed to see.

Running the pre-built Docker image
----------------------------------

::

  docker run --name knutj42/sesam-jira-currenttime-webserver -p 8080:8080



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
  docker run --name sesam-jira-currenttime-webserver -p 8080:8080

Get the IP from docker:

::

  docker inspect -f '{{.Name}} - {{.NetworkSettings.IPAddress }}' sesam-jira-currenttime-webserver

