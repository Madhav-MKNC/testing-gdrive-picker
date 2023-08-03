from google_auth_oauthlib.flow import Flow
from flask import Flask, request, redirect, session
from flask import render_template

from flask import render_template
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

import io
from googleapiclient.http import MediaIoBaseDownload

from flask_cors import CORS

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

app.secret_key = 'some'  # replace with your secret key

@app.route('/')
def index():
    if 'credentials' not in session:
        return redirect('authorize')
    else:
        # Load credentials from the session
        credentials = Credentials(**session['credentials'])

        # Build the Drive service
        drive_service = build('drive', 'v3', credentials=credentials)

        # Get the list of files from Google Drive
        results = drive_service.files().list(pageSize=10).execute()
        items = results.get('files', [])

        return render_template('logged_in.html', items=items)


@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive', 'openid'],
        redirect_uri='http://localhost:5000/oauth2callback'
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive', 'openid'],
        state=state,
        redirect_uri='http://localhost:5000/oauth2callback'
    )
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect('/')



@app.route('/upload', methods=['POST'])
def upload():
    if 'credentials' not in session:
        return redirect('authorize')
    else:
        # Load credentials from the session
        credentials = Credentials(**session['credentials'])

        # Build the Drive service
        drive_service = build('drive', 'v3', credentials=credentials)

        # Get the ID of the file to upload
        data = request.get_json()
        file_id = data['fileId']

        # Request the file from the Drive API
        request = drive_service.files().get_media(fileId=file_id)

        # Download the file
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Save the file to disk
        with open(f'{file_id}', 'wb') as f:
            f.write(fh.getbuffer())

        return "File uploaded successfully"








if __name__ == '__main__':
    app.run('localhost', 5000, debug=True)
