# async-file-processor

**async-file-processor** is a monolithic project which is in charge of processing files to be later changed extension, these files are glued in a pub/sub in google cloud, once glued, the same application consumes this topical to obtain the file, or transform and store it.

**technologies**

* Docker
* Python
* Flask
* Flask-JWT
* Flask-RESTfull
* celery
* pytest
* moviepy
