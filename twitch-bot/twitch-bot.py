#
# Author: Nick Quinn (FreakyNobleGas)
#
# Description: This program notifies Discord servers when a Twitch broadcaster goes live. The
#              names of the Discord servers and associated broadcasters are defined in a file
#              named 'discord_servers.json'.
#

from os import getenv
from dotenv import load_dotenv
from twitchAPI import Twitch, EventSub
from pyngrok import ngrok
import requests
from json import loads

# Grab secret env variables
load_dotenv()

# Global Configuration Variables
PORT = 8080
APP_ID = getenv('CLIENT_ID')
APP_SECRET = getenv('SECRET')
NGROK_AUTH_TOKEN = getenv('NGROK')

# Discord Server Webhooks
with open('discord_servers.json', 'r') as f:
    data=f.read()

discord_webhooks = loads(data)

# Setting an auth token allows us to open multiple
# tunnels at the same time
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# Open a HTTP tunnel on the port defined by PORT variable
# <NgrokTunnel: "http://<public_sub>.ngrok.io" -> "http://localhost:80">
http_tunnel = ngrok.connect(addr=str(PORT))

WEBHOOK_URL = str(http_tunnel.public_url)
WEBHOOK_URL = WEBHOOK_URL.replace('http', 'https')

# Twitch Client
twitch = Twitch(APP_ID, APP_SECRET)
twitch.authenticate_app([])

# Basic setup, will run on port 8080 and a reverse proxy takes care of the https and certificate
hook = EventSub(WEBHOOK_URL, APP_ID, PORT, twitch)
hook.wait_for_subscription_confirm = False

# Unsubscribe from all to get a clean slate
hook.unsubscribe_all()

# Start client
hook.start()

async def stream_goes_live(data: dict):
    try:
        broadcaster = data.get('event', {}).get('broadcaster_user_name')
        print(f"INFO: {broadcaster} just went live.")

        broadcaster_url = f"https://www.twitch.tv/{broadcaster}"

        # Retrieve all servers from configuration file and check if the broadcaster is listed as a user. If
        # user is listed, then notify server.
        servers = discord_webhooks.get("servers")
        for server in servers:

            users = server.get("users")
            for user in users:

                if broadcaster.lower() == user.lower():
                    name = server.get("name")
                    print(f"INFO: Sending notification to server {name}")

                    data = {
                        "content": f"{broadcaster} is live on Twitch! Mmkay..\n\n{broadcaster_url}",
                        "username": "Mr. Mackey",
                        "avatar_url": 'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse4.mm.bing.net%2Fth%3Fid%3DOIP.d9xKENKP7Imez7-nCduW0wHaEK%26pid%3DApi&f=1',
                        "embeds": []
                    }

                    result = requests.post(server.get("webhook_url"), json=data)

                    if 200 <= result.status_code < 300:
                        print(f"Webhook sent {result.status_code}")
                    else:
                        print(f"Not sent with {result.status_code}, response:\n{result.json()}")

    except Exception as e:
        print("ERROR: stream_goes_live function hit unexpected error.\n", e)
    
print('INFO: Subscribing to hooks.')

# Hook Broadcasters
for broadcaster in discord_webhooks.get('broadcasters', []):
    print(f"INFO: Subscribing to {broadcaster}")
    uid = twitch.get_users(logins=[broadcaster])
    broadcaster_id = uid['data'][0]['id']
    hook.listen_stream_online(broadcaster_id, stream_goes_live)

try:
    # Wait for user hit any key (except control+C) to end program
    print("INFO: Listening for events... press any button to end program (except control+c)")
    input()
finally:
    hook.stop()

print('INFO: Done')
