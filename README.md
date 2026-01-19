# Setting up
## Discord
1. Create a application in the dev portal
2. Create a bot
3. Get the token for the bot
4. Put bot token in .env as `DISCORD_BOT_TOKEN`
5. Put the channel you want to make the status channel in .env as `DISCORD_STATUS_CHANNEL_ID`
## Firebase
1. Create a Firebase project
2. In the firebase project, create a Realtime Database
3. Generate a service account private key, save it to `./firebase-credentials`
4. Copy firebase URL to a new file `.env` as `FIREBASE_URL` and put that same URL as `FIREBASE_URL` in the form.gs file

## Google Forms
1. Link both forms to the same spreadsheet
2. Set the sign-in sheet's name to be "Sign In"
3. Set the sign-out sheet's name to be "Sign Out"
4. Create an Apps Script for the spreadsheet by doing Extensions > Apps Script
5. Add the `private_key` prop in `firebase-credentials.json` as `PRIVATE_KEY` and the `client_email` prop as `CLIENT_EMAIL` in the Apps Script configuration as properties (click the gear icon on the left)
6. Copy the form.gs file into teh Google Apps Script default `Code.gs` file
7. Add a trigger (the alarm icon) to call `onFormSubmit` for the event `From Spreadsheet - On Form Submit`
8. Test that firebase works by running the `testFirebaseConnection` function manually

## The Python Program
1. install python and tk (distro dependent, on apt you need python3-tk)
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `python3 kiosk.py`
