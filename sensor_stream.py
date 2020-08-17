# project
from occupancy.director import Director

# Fill in from the Service Account and Project:
USERNAME   = "brn1e6r24te000b24bp0"             # this is the key
PASSWORD   = "34fc21309a8e462cb491a0d7610ea489" # this is the secret
PROJECT_ID = "brn0ti14jplfqcpojb60"            # this is the project id

# url base and endpoint
API_URL_BASE  = "https://api.disruptive-technologies.com/v2"


if __name__ == '__main__':

    # initialise Director instance
    d = Director(USERNAME, PASSWORD, PROJECT_ID, API_URL_BASE)

    # iterate historic events
    d.event_history()

    # stream realtime events
    d.event_stream(n_reconnects=5)

