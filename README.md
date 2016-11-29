[![Docker Repository on Quay](https://quay.io/repository/signrequest/signrequest-event-receiver/status "Docker Repository on Quay")](https://quay.io/repository/signrequest/signrequest-event-receiver)

# SignRequest event receiver server example

Example SignRequest event receiver to async handle SignRequest events and do some work accordingly. Learn more about SignRequest event callbacks here: https://signrequest.com/api/v1/docs/

This is the source for the image pushed to `quay.io/signrequest/signrequest-event-receiver:v1` 
see: https://quay.io/repository/signrequest/signrequest-event-receiver

The webserver is powered by [Tornado](http://www.tornadoweb.org/), runs on python 3.5 and uses `async` and `await` to make HTTP requests non-blocking. 

The only example currently implemented here is uploading signed documents to [BambooHR](https://www.bamboohr.com/). However by implementing your own handler you can do other work after the event is received.

The image should always be run with the `SIGNREQUEST_TOKEN` environment variable as the receiver validates that the POST request from SignRequest is genuine. 

## BambooHR
The BambooHR handler syncs all signed documents, signed by signers that are not the sender and have an Employee record, to BambooHR.
This can be useful if you want to sync all documents signed within a SignRequest Team to employees in BambooHR.

To run the event receiver for BambooHR a couple of extra environment variables are required:
- `BAMBOO_TOKEN`: The API token of your BambooHR account
- `BAMBOO_SUBDOMAIN`: The subdomain of your BambooHR company account
- `BAMBOO_FILE_CATEGORY_ID` (optional, default: 2): The file category ID (folder) where to store the files to.
- `BAMBOO_SHARE_WITH_EMPLOYEE` (optional, default: 0): Set to 1 to share the files uploaded with the employee.

### Running
The container exposes and runs the webserver on port 8888 internally. The following examples also binds the host port 8888 to the container.
To run this without building the docker image from this source you can run the following command for running in daemon mode:

```sh
docker run --restart=always -d -p 8888:8888 -e SIGNREQUEST_TOKEN='your signrequest token' -e BAMBOO_TOKEN='your token' -e BAMBOO_SUBDOMAIN='your_subdomain' quay.io/signrequest/signrequest-event-receiver:v1
```

Or for interactive debug mode:

```sh
docker run -it -p 8888:8888 -e SR_RECEIVER_DEBUG=1 -e SIGNREQUEST_TOKEN='your signrequest token' -e BAMBOO_TOKEN='your token' -e BAMBOO_SUBDOMAIN='your_subdomain' quay.io/signrequest/signrequest-event-receiver:v1
```

When you have the server running somewhere you'll need to setup the `events callback url` setting in your SignRequest Team settings page to point to the `bamboohr` endpoint on  your server:
https://example.com/bamboohr

Now all documents that get signed will trigger an event POST from SignRequest to this server and the files will be synced to BambooHR.

# Help
Why is this here? Need help? I want more handlers!? Contact us on api@signrequest.com, we're happy to help! :)
