import pyodbc
import os
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#########################################################################################
#                                  KeyInfo Class                                        #
#########################################################################################

class KeyInfo:
    def __init__(self, TicketId, KeyName, Password, Email):
        self.TicketId = TicketId
        self.KeyName = KeyName
        self.Email = Email
        self.Password = Password

def Generate(keyInfo):
