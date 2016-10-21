========================
JIRA/CurrentTime example
========================

This is an example project that uses SESAM to compare the hours logged in JIRA and in CurrentTime.

.. contents:: Table of Contents
   :depth: 2
   :local:


Overview
--------

The problem
~~~~~~~~~~~

In Bouvet the consultants often have to log hours in two systems:

**JIRA:**

This is a bug/task tracking system. Here the consultants log how many hours they spent on each bug/task.

**CurrentTime:**

This is an time-tracking system. Here the consultants log how many hours they used on each project. 

The norm in Bouvet is that CurrentTime is used to bill the customers, so it is important that all 
hours are logged there. But we also want to keep track of how much time was spent on each task in 
JIRA, so we want to log hours in JIRA, too.

This causes problems, since it is time-consuming and error-prone to manually make sure that the 
number of hours in JIRA and CurrentTime matches up.

We therefore want to automate this process.

The simplest check is to make sure that the total number of hours for each user and date is the same
in JIRA and in CurrentTime (not including entries in CurrentTime that are never connected to JIRA
tasks ("Lunch", "Doctors appointment", etc). This is straight forward, but it is not a very fine-grained
approach. Ideally, we would like to be able to figure out which CurrentTime Subtask should be used to log
the hours in each JIRA-issue. Unfortunatly, there is no built-in way to doing this in JIRA or CurrentTime;
the two systems do not communicate directly with each other in any way. 

We must therefore connect JIRA-issues with CurrentTime subtasks it in a more 'un-official' way. 

One commonly used method is to type in the JIRA issue-key when logging hours in CurrentTime, like this:

.. image:: ./currenttime_note_with_jira_issue_key.png

In this case we want to find all CurrentTime worklog entries that refer to one or
more JIRA-issues and check that the number of hours in the CurremtTime worklog entry matches the 
total number of hours logged in the JIRA issues during that same day.
  
The solution
~~~~~~~~~~~~  

The solution to the problem is to have SESAM create cvs files that list the discrepancies between
JIRA and CurrentTime. CSV-files are a nice format because they can be easily imported into 
MSExcel and manipulated (sorted, filtered, etc) by non-technical people. We can therefore get away 
with not implementing any GUI ourselves, since Excel can do everything we need.

We currently produce two CVS-files. They are both semi-colon separated, and uses UTF-8 character
encoding.

**"compare-totals.csv"**

This file lists the differences between the total number of hours in JIRA and CurrentTime. There is one
line for each user+date combination. The file looks like this::

    Date;Username;Errors;JIRA hours;CT hours
    2016-10-10;jon.snow;The total number of hours logged in CurrentTime and JIRA are not identical. JIRA: 5 hours. CurrentTime: 7.5 hours;5;7,5
    2016-09-28;gregor.clegane;The total number of hours logged in CurrentTime and JIRA are not identical. JIRA: 4 hours. CurrentTime: 12 hous;1;7
    ...

**"workentries-in-currenttime-with-errors.csv"**:

This file lists problems for CurrentTime entries that refer to a jira issue-key ("SSD-123", IS-456", etc).
The file looks like this::

    Date;Username;Errors;CT hours;JIRA hours;CT subtask;CT task;CT project;CT projecttype;CT note;JIRA keys
    2016-10-05;jon.snow;No hours has been logged in JIRA for this JIRA-issue: BKKI-12345;6,5;0;konsulentbistand;Forvaltning;BKK forvaltning (5896);Eksterne kunder løpende timer;BKKI-12345;BKKI-12345
    2016-09-23;gregor.clegane;The 'note'-field in CurrentTime refer to this non-existing JIRA-issue: SA-12345;2;0;Appl.Forv. - Løpende;Appliksasjonsforvaltning;Alere (6890) Forvaltning/Drift/Overvåkning;Eksterne kunder Forvaltning;SA-12345;SA-12345
    2016-10-10;gregor.clegane;The hours logged in CurrentTime and JIRA are not identical. JIRA: 5 hours. CurrentTime: 7.5 hours;7,5;5;Utvikling Sesam-ansatte;Utvikling;Sesam Utvikling (8885);Interne kunder løpende timer;IS-12345;IS-12345


Implementation details / logic
------------------------------

This section contains a detailed description on how we use SESAM to produce the CSV files.

Data import ("jira-*" and "currenttime-*")
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SESAM connects directly to the JIRA and CurrentTime databases. 

Each "jira-<tablename>" pipe reads from the one JIRA database table and stores the raw data in a dataset.

Each "currenttime-<tablename>" pipe reads from the one CurrentTime database table and stores the raw data in a dataset.

The most important of these are the "jira-worklog" and "jira-timetransaction" pipes. These tables contain 
the actual information about hours worked, and are the ones where the content is most frequently modified.

The "jira-worklog" and "jira-timetransaction" pipe are configured to run every five minutes, so that 
SESAM's information is reasonably up-to-date. The other "jira-*" and "currenttime-*" pipes are run once 
per hour, since the data in the corresponding tables changes much more rarely (and we don't want to
spam the database servers with unnecessary queries). 

Cooking the raw data (cooked-\*)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For some of the source-tables we want to add a bit of denormalized information. This is done by the
"cooked-\*" pipes:

"cooked-jira-jiraissue": 
Adds a "jira_issue_key" attribute with the JIRA-key of the jira-issue by doing a lookup in the "jira-project"
dataset. The JIRA-key is the "<PROJECT_ABBREVIATION>-<issue_number>" that the user sees the the 
JIRA web interface (examples: "SESAM-42", "IBB-232").

"cooked-currenttime-project":
Adds a "projecttypename" attribute by doing a lookup in the "currenttime-projecttype" dataset.

"cooked-currenttime-subtask":
Adds "taskname", "projectname" and "projecttypename" attributes by doing lookups in the 
"currenttime-task" and "cooked-currenttime-project" datasets.


Creating "workentry-currenttime"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 
In this flow we want to take the raw data and create a dataset with one entity for each user+day+currenttime_subtask
combination. The "_id" attribute of the resulting entities are on the form "<user_name>--<date>--<currenttime_subtask_id>".

This is straightforward, since each entity in the "currenttime-timetransaction" maps directly to what
we want. The "workentry-currenttime" pipe just have to collect some extra information from other datasets 
(for instance getting the "user_email" attribute from the "currenttime-employee" dataset). 

We also filter out entries where the currenttime_subtask refers to some internal activity that will not have a 
JIRA-task ("Lunch", "Doctor's appointment", etc). This is done by checking if the projecttypename of the
currenttime-subtask exists in the hardcoded "config-internal-projecttype-names" dataset.


Creating "workentry-jira"
~~~~~~~~~~~~~~~~~~~~~~~~~

In this flow we want to take the raw data and create a dataset with one entity for each user+day+jira_issue
combination. This is a bit tricker than for "workentry-currenttime", since there can be multiple entries in 
"jira-worklog" for each jira-issue for the same day.

We must therefore do this operation in several steps. These are implemented in the "workentry-jira-step*"
pipes, where each pipe reads the input from the previous step:

#. `workentry-jira-step1-cook-jira-worklog <./sesam-conf/pipes/workentry-jira-step1-cook-jira-worklog.conf.json>`_
#. `workentry-jira-step2-unique_workentry_ids <./sesam-conf/pipes/workentry-jira-step2-unique_workentry_ids.conf.json>`_
#. `workentry-jira-step3-merge-worklog-entities  <./sesam-conf/pipes/workentry-jira-step3-merge-worklog-entities.conf.json>`_



Creating "workentry-total-currenttime"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this flow we want to create a dataset where each entity represents all the work one user has logged
per day in currenttime, across all currenttime projects and tasks. We do this in a similar way to the
"workentry-jira" flow, with three pipes:

#. `workentry-total-currenttime-step1-cook <./sesam-conf/pipes/workentry-total-currenttime-step1-cook.conf.json>`_
#. `workentry-total-currenttime-step2-unique-workentry_total_id <./sesam-conf/pipes/workentry-total-currenttime-step2-unique-workentry_total_id.conf.json>`_
#. `workentry-total-currenttime-step3-merge <./sesam-conf/pipes/workentry-total-currenttime-step3-merge.conf.json>`_


Creating "workentry-total-jira"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this flow we want to create a dataset where each entity represents all the work one user has logged
per day in JIRA, across all JIRA issues. The procedure is identical to how "workentry-total-currenttime"
is created; We aggregate the values in the "workentry-jira" dataset for each user_name+date combination, using
three pipes:

#. `workentry-total-jira-step1-cook <./sesam-conf/pipes/workentry-total-jira-step1-cook.conf.json>`_
#. `workentry-total-jira-step2-unique-workentry_total_id <./sesam-conf/pipes/workentry-total-jira-step2-unique-workentry_total_id.conf.json>`_
#. `workentry-total-jira-step3-merge <./sesam-conf/pipes/workentry-total-jira-step3-merge.conf.json>`_

The results end up in the "workentry-total-jira-step3-merge" dataset.


Finding errors in currenttime worklog entries with JIRA-keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is done by the "workentry-currenttime-with-jira-keys-step*" pipes. 

#. `workentry-currenttime-with-jira-keys-step1-note-filter <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step1-note-filter.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step2-jiraissue-keys <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step2-jiraissue-keys.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step3-jiraissue-keys-filter <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step3-jiraissue-keys-filter.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step4-create-jiraissue-keys-children <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step4-create-jiraissue-keys-children.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step5-emit-jiraissue-keys-children <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step5-emit-jiraissue-keys-children.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step6-lookup-jira-hours <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step6-lookup-jira-hours.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step7-compare-hours <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step7-compare-hours.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step8-has-errors-filter <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step8-has-errors-filter.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step9-add-task-and-project-info <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step9-add-task-and-project-info.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step10-csv-format <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step10-csv-format.conf.json>`_
#. `workentry-currenttime-with-jira-keys-step11-csv <./sesam-conf/pipes/workentry-currenttime-with-jira-keys-step11-csv.conf.json>`_

workentry-currenttime-with-jira-keys-step11-csv

Finding errors in the total number of hours in JIRA and CurrentTime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As a rule, the total number of hours in JIRA and in CurrentTime (minus hours on internal projects) should match.
To check this we compare the entities in the "workentry-total-jira-step3-merge" and "workentry-total-currenttime-step3-merge"
datasets and check that the number of hours are the same in both. 

This check is done by the following pipes:

#. `compare-totals-step1-merge <./sesam-conf/pipes/compare-totals-step1-merge.conf.json>`_. 
   This pipe uses the "merge_dataset" source to gather corresponding entities from the 
   "workentry-total-jira-step3-merge" and "workentry-total-currenttime-step3-merge"
   datasets. 
#. `compare-totals-step2-compare-hours <./sesam-conf/pipes/compare-totals-step2-compare-hours.conf.json>`_
#. `compare-totals-step3-has-errors-filter <./sesam-conf/pipes/compare-totals-step3-has-errors-filter.conf.json>`_
#. `compare-totals-step4-csv-format <./sesam-conf/pipes/compare-totals-step4-csv-format.conf.json>`_
#. `compare-totals-step5-csv <./sesam-conf/pipes/compare-totals-step5-csv.conf.json>`_.
   This pipe publishes the dataset of the previous pipe as a CSV-file at this url:
   `<http://localhost:9042/api/publishers/compare-totals-step5-csv/csv>`_



How to run the SESAM installation
---------------------------------

If you haven't already done so, go to the `Sesam Portal website <https://portal.sesam.in>`_ and follow the instructions
there to get a SESAM instance up and running.

Then, install the SESAM commandline client as described `here <https://docs.sesam.io/overview.html#getting-started>`_.

The trickiest part of running this SESAM installation is that you need to have a database user account with
read-permissions to both the JIRA and CurrentTime databases. You will have to talk to the person(s) administering
the JIRA and CurrentTime installations you want to connect to. 

Once you have gotten usernames and passwords for the JIRA and CurrentTime databases you can fill in
the placeholder values in these files:

`<./sesam-conf/environment_variables.json>`_

`<./sesam-conf/secrets.json>`_

Open a terminal and go to the "sesam-jira-currenttime-example/sesam-conf" folder. Run the following commands::

    $ sesam put-secrets secrets.json
    $ sesam put-env-vars environment_variables.json
    $ sesam import .

That is all that is required. The csv-files will eventually be available. However, some of the pipes only
run once per day, since some of the data that rarely changes in JIRA and CurrentTime. To avoid having to
wait for several hours, you should use the management studio (which is running on `<http://localhost:9042/>`_)
to start all the pipes with ids that starts with "jira-" or "currenttime-". Depending on the amount of data
some of the pipes can take a long to run (minutes or hours).

Optionally, you can also start the webserver that provides cvs-files that are filtered to only return information
relevant to the currently logged in user. This is described in the `webserver README-file <./webserver/README.rst>`_.




Output
------

The csv-file that contains the errors in CurrentTime entries that refer to JIRA-tasks is served on this url:

   `<http://localhost:9042/api/publishers/workentries-in-currenttime-with-errors-csv/csv>`_


The csv-file that contains the mismatches between total number or hours logged in JIRA and in CurrentTime
is served on this url:

   `<http://localhost:9042/api/publishers/compare-totals-step5-csv/csv>`_


This files can be retrieved by opening the url in a web-browser. Some web-browsers will just download the csv-file 
to your "Downloads" folder, others will display the content of the file. 

The files can of course also be downloaded with a commandline tool:

On Linux, open a terminal and run this command::
   
   curl -o errors.csv "http://localhost:9042/api/publishers/workentries-in-currenttime-with-errors-csv/csv"

On Windows, start PowerShell and run this command::

   Invoke-WebRequest -Uri "http://localhost:9042/api/publishers/workentries-in-currenttime-with-errors-csv/csv"  -OutFile errors.csv

  
The cvs-files are fairly big and human unfriendly, but a good way to view them is to open the files in Microsoft Excel and
use Excel's functionality to do searching, filtering and sorting.
