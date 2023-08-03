from flask import Flask, request, redirect, session, render_template
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
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
        return render_template('logged_in.html')


@app.route('/files')
def files():
    page = request.args.get('page', 1, type=int)

    if 'credentials' not in session:
        return redirect('authorize')
    else:
        # Load credentials from the session
        credentials = Credentials(**session['credentials'])

        # Build the Drive service
        drive_service = build('drive', 'v3', credentials=credentials)

        # Keep track of the next page token for pagination
        next_page_token = session.get('nextPageToken', None)

        # Get the list of files from Google Drive
        results = drive_service.files().list(pageSize=10, pageToken=next_page_token).execute()
        items = results.get('files', [])
        next_page_token = results.get('nextPageToken', None)

        session['nextPageToken'] = next_page_token

        return render_template('files.html', items=items, next_page_token=next_page_token is not None)


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

@app.route('/download', methods=['POST'])
def download():
    if 'credentials' not in session:
        return redirect('authorize')
    else:
        # Load credentials from the session
        credentials = Credentials(**session['credentials'])

        # Build the Drive service
        drive_service = build('drive', 'v3', credentials=credentials)

        # Get the ID of the file to download
        data = request.get_json()
        file_id = data['fileId']

        # Generate the download link
        download_link = drive_service.files().get(fileId=file_id, fields='webContentLink').execute()['webContentLink']

        return {'downloadLink': download_link}



if __name__ == '__main__':
    app.run('localhost', 5000, debug=True)
