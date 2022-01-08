import os.path
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheet:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(
        self, sheet_id, token_file, cred_file=None, new_token_name="token.json"
    ):
        self.sheet_id = sheet_id
        self.creds = None
        self.new_token_name = new_token_name
        self.row = []
        self._authenticate(token_file, cred_file)
        self.setup()

    def _authenticate(self, token_file, cred_file=None):
        self.creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                self._flow = InstalledAppFlow.from_client_secrets_file(
                    cred_file, self.SCOPES
                )
                self.creds = self._flow.run_local_server(port=0)
            with open("new-token.json", "w") as token:
                token.write(self.creds.to_json())

    def add_value(self, *args):
        for value in args:
            self.row.append(value)

    def setup(self):
        self._service = build("sheets", "v4", credentials=self.creds)

        # Call the Sheets API
        self.sheet = self._service.spreadsheets()

    def read(self, range=None):
        result = (
            self.sheet.values().get(spreadsheetId=self.sheet_id, range=range).execute()
        )
        values = result.get("values", [])

        if not values:
            return
        return values

    def commit(self, range, input_option="RAW"):
        values = [[datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"), *self.row]]
        body = {"values": values}
        result = (
            self.sheet.values()
            .append(
                spreadsheetId=self.sheet_id,
                valueInputOption=input_option,
                range=range,
                body=body,
            )
            .execute()
        )
        print("{0} cells appended.".format(result.get("updates").get("updatedCells")))
