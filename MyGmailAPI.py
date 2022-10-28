
from __future__ import print_function
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bs4 import BeautifulSoup
import base64
import email

import pandas as pd
import numpy as np
import time

'''
Listing various functions in here to keep the notebook cleaner.
If there were plans to improve this we might create class so that we can just call 
funtions and attributes.
'''

class GmailAPI(object):
    ''' GMAIL API CALL
        SCOPES = the scope call
        CREDS = credentials json file
        SERVICE = service call
    '''
    def __init__(self, scopes, creds, service):
        self.scopes = scopes
        self.creds = creds
        self.service = service        


    def get_results(self, iters=10, label_filter=None):
        ''' Gets Results
            Params:
            = = = = = = = = = = = = = = = = = = = = 
            iters = max number of iters to run while checking nextPageToken

            Returns:
            = = = = = = = = = = = = = = = = = = = = 
            all_msgs = all messages list of data frames
        '''
    #     SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    #     creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    #     service = build('gmail', 'v1', credentials=creds)
    
        SCOPES = self.scopes
        creds = self.creds
        service = self.service

        pageToken = None
        messages_left = True

        all_msgs = []
        # Get messages
        while (messages_left) and (iters > 0):
            results = service.users().messages().list(maxResults=500, includeSpamTrash=True,
                                                      labelIds=label_filter,
                                                      userId="me", pageToken=pageToken).execute()
            pageToken = results.get('nextPageToken')
            # do something with the messages! Importing them to your database for example

            clean_msgs = self.extract_data(results, service)
            clean_df = pd.DataFrame(clean_msgs, columns=['subject',#'body',
                                                         'sender','snippet',
                                                         'labels'
                                                        ])
            all_msgs.append(clean_df)

            iters -= 1
            if not pageToken:
                mesages_left = False
    #     results = service.users().messages().list(maxResults=n_results, userId='me').execute()
    
        self.all_messages_cleaned = all_msgs
        return all_msgs


    def extract_data(self, results, service):
        ''' Function to pull in messages details.
            Params:
            = = = = = = = = = = = = = = = = = = = =
            results = results from api call

            Returns:
            = = = = = = = = = = = = = = = = = = = =
            List of message details per message
        '''   
        
        service = self.service
        
        messages = results.get('messages')
        all_msgs = []
        start_time = time.time()
        for msg in messages:
            # Get the message from its id
            txt = service.users().messages().get(userId='me', id=msg['id'],
                                                 format="full", metadataHeaders=None).execute()   

            ## set defaults to not confuse emails and re-use variables if others are missing
            subject, sender, snippet, labels = '', '', '', ['']

            payload = txt['payload']
            headers = payload['headers']
            snippet = txt['snippet']
            labels = txt['labelIds']

            chat_count = 0
            if 'CHAT' in str(txt['labelIds']):
                chat_count += 1
                pass
            else:
                # Look for Subject and Sender Email in the headers
                for d in headers:
                    if d['name'] == 'Subject':
                        subject = d['value']
                    if d['name'] == 'From':
                        sender = d['value']

                try:
                    all_msgs.append([subject, #body, 
                                     sender, snippet, labels])
                except:
                    pass
                    ## skip ones that arent complete?

        print(f"Chat count = {chat_count}")
        print(f"time to complete = {(time.time() - start_time)/60 :.3f} mins")
        return all_msgs
