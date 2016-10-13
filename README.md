# JIRA/CurrentTime example

This is an example project that uses SESAM to compare the hours logged in JIRA and in CurrentTime.

##Overview
In Bouvet the consultants often have to log hours in two systems:

JIRA:
This is a bug/task tracking system. Here the consultants log how many hours they spent on each bug/task.

CurrentTime:
This is an time-tracking system. Here the consultants log how many hours they used on each project. 

The norm in Bouvet is that CurrentTime is used to bill the customers, so it is important that all 
hours are logged there. But we also want to keep track of how much time was spent on each task in 
JIRA, so we want to log hours in JIRA, too.

This causes problems, since it is time-consuming and error-prone to manually make sure that the 
number of hours in JIRA and CurrentTime matches up.

We therefore want to automate this process.
 
First, we need some way to connect the hours in JIRA with the hours in CurrentTime. There are no 
built-in way to doing this in JIRA or CurrentTime; the two systems do not communicate directly with 
each other in any way. We must therefore do it in a more 'un-official' way. 

One commonly used method is to type in the JIRA issue-key when logging hours in CurrentTime, like this:

![CurrentTime note with a reference to a JIRA issue](currentime_note_with_jira_issue_key.png)

In this case we want to find all CurrentTime worklog entries that refer to one or
more JIRA-issues and check that the number of hours in the CurremtTime worklog entry matches the 
total number of hours logged in the JIRA issues during that same day.
  
  
Another check is to make sure that the total number of hours for each user and date is the same
in JIRA and in CurrentTime (not including entries in CurrentTime that are never connected to JIRA
tasks ("Lunch", "Doctors appointment", etc).

  

## Implementation details / logic

### Data import ("jira-*" and "currenttime-*")

SESAM connects directly to the JIRA and CurrentTime databases. 

Each "jira-<tablename>" pipe reads from the one JIRA database table and stores the raw data in a dataset.

Each "currentime-<tablename>" pipe reads from the one CurrentTime database table and stores the raw data in a dataset. 

The most important of these are the "jira-worklog" and "jira-timetransaction" pipes. These tables contain 
the actual information about hours worked, and are the ones where the content is most frequently modified.

The "jira-worklog" and "jira-timetransaction" pipe are configured to run every five minutes, so that 
SESAM's information is reasonably up-to-date. The other "jira-*" and "currenttime-*" pipes are run once 
per hour, since the data in the corresponding tables changes much more rarely (and we don't want to
spam the database servers with unnecessary queries). 

### Cooking the raw data ("cooked-*")

For some of the source-tables we want to add a bit of denormalized information. This is done by the
"cooked-*" pipes:

"cooked-jira-jiraissue": 
Adds a "jira_issue_key" attribute with the JIRA-key of the jira-issue by doing a lookup in the "jira-project"
dataset. The JIRA-key is the "<PROJECT_ABBREVIATION>-<issue_number>" that the user sees the the 
JIRA web interface (examples: "SESAM-42", "IBB-232").

"cooked-currenttime-project":
Adds a "projecttypename" attribute by doing a lookup in the "currenttime-projecttype" dataset.

"cooked-currenttime-subtask":
Adds "taskname", "projectname" and "projecttypename" attributes by doing lookups in the 
"currenttime-task" and "cooked-currenttime-project" datasets.


### Creating "workentry-currenttime"
 
In this flow we want to take the raw data and create a dataset with one entity for each user+day+currentime_subtask
combination. The "_id" attribute of the resulting entities are on the form "<user_name>--<date>--<currenttime_subtask_id>".

This is straightforward, since each entity in the "currentime-timetransaction" maps directly to what
we want. The "workentry-currenttime" pipe just have to collect some extra information from other datasets 
(for instance getting the "user_email" attribute from the "currenttime-employee" dataset). 

We also filter out entries where the currenttime_subtask refers to some internal activity that will not have a 
JIRA-task ("Lunch", "Doctor's appointment", etc).



### Creating "workentry-jira"

In this flow we want to take the raw data and create a dataset with one entity for each user+day+jira_issue
combination. This is tricker than for "workentry-currenttime", since there can be multiple entries in 
"jira-worklog" for each jira-issue for the same day.

We must therefore do this operation in several steps. These are implemented in the "workentry-jira-step*"
pipes, where each pipe reads the input from the previous step.

"workentry-jira-step1-cook-jira-worklog":
Reads from "jira-worklog" and adds various extra attributes ("user_name", "jira_issue_key", etc).
It also adds a "workentry_id" attribute. This contains a string on the form "<user_name>--<date>--<jira_issue_key>". 
This string will becode the "_id" value of the entities in the final "worklog-jira" dataset.

"workentry-jira-step2-unique_workentry_ids":
Reads from the "workentry-jira-step1-cook-jira-worklog" dataset and creates entities with "_id" set 
to the "workentry_id" attribute that was created in the previous step. This has the effect of creating 
as dataset with one entity per user+day+jira_issue combination; if this pipe produces more than one
entity with the same "_id" (which happens if the user has several work-log entries on the JIRA-issue for
the same day), each duplicate entity will just overwrite the previous version of the entity.
  
"workentry-jira-step3-merge-worklog-entities":
Reads from the "workentry-jira-step2-unique_workentry_ids" dataset and looks up all the entities from 
the "workentry-jira-step1-cook-jira-worklog" dataset where the "workentry_id" attribute matches the
"_id" from the source entity. Then it calculates the total number of hours from all those entities.


### Creating "workentry-total-currenttime"

In this flow we want to create a dataset where each entity represents all the work one user has logged
per day in currenttime, across all currenttime projects and tasks. We do this in a similar way to the
"workentry-jira" flow:

"workentry-total-currenttime-step1-cook":
Reads from "workentry-currenttime" and adds a "workentry_total_id" that is on the form "<user_name>--<date>". 

"workentry-total-currenttime-step2-unique-workentry_total_id":
Reads from "workentry-total-currenttime-step1-cook" and creates entities with the "_id" set to the value
of the "workentry_total_id" attribute that was created in the previous step.

"workentry-total-currenttime-step3-merge":
Reads from "workentry-total-currenttime-step2-unique-workentry_total_id" and looks up all the entities in
"workentry-total-currenttime-step1" where the "workentry_total_id" attribute matches the "_id" attribute 
of the source entity. Store the sum of the time worked.


### Creating "workentry-total-jira"

In this flow we want to create a dataset where each entity represents all the work one user has logged
per day in JIRA, across all JIRA issues. The procedure is identical to how "workentry-total-currenttime"
is created, so we won't re-hash the details here. In short, we aggregate the values in the "workentry-jira"
dataset for each user_name+date combination.


### Finding errors in currenttime worklog entries with JIRA-keys



## How to run the SESAM installation

TODO

## Output

The final product is a csv-file containing all mismatches. It is served on this url: 

  `http://localhost:9042/api/publishers/workentries-in-currenttime-with-errors-csv/csv`

This file can be retrieved by pasting the url into a web-browser. Alternativly, it can be downloaded with a commandline tool:

On Linux, open a terminal and run this command:
   `curl -o errors.csv "http://localhost:9042/api/publishers/workentries-in-currenttime-with-errors-csv/csv"`

On Windows, start PowerShell and run this command: 
  `Invoke-WebRequest -Uri "http://localhost:9042/api/publishers/workentries-in-currenttime-with-errors-csv/csv"  -OutFile errors.csv`

  
The resulting cvs-file is fairly big and human unfriendly, but a good way to view it is to open the file in Microsoft Excel and
use Excel's functionality to do searching, filtering and sorting.  

