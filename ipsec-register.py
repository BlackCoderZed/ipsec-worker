from suds.client import Client
import os
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import string
import random
from pathlib import Path

#########################################################################################
#                                  KeyInfo Class                                        #
#########################################################################################

class KeyInfo:
    def __init__(self, TicketId, KeyName, Password, Email):
        self.TicketId = TicketId
        self.KeyName = KeyName
        self.Email = Email
        self.Password = Password


def StartOperation(serverID):
    ticketInfoList = GetTicketInfo(serverID)
    for ticketInfo in ticketInfoList:
        isSuccess = RegisterUser(ticketInfo)
        if (isSuccess == True):
            print("User Registeration success")
            ExportToFile(ticketInfo)
            UpdateTicketInfo(ticketInfo)
            SendMail(ticketInfo)

# Get Instruction List
def GetTicketInfo(serverId):
    authInfo = AUTH_INFO
    reqInfo = REQ_INFO
    ticketInfoLst = []
    wsdl = "http://13.231.65.63:8999/VPNAPIService.svc?wsdl"
    client = Client(wsdl)
    result = client.service.GetInstructionInfoList(authInfo, reqInfo)

    if(result.InstructionList is None or len(result.InstructionList) <= 0):
        return ticketInfoLst

    for instList in result.InstructionList:
        for inst in instList[1]:
            ticketId = inst[0]
            keyName = inst[2]
            email = inst[3]
            kInfo = KeyInfo(ticketId, keyName, '', email)
            ticketInfoLst.append(kInfo)
    
    return ticketInfoLst

# Instruction Status Update
def UpdateTicketInfo(ticketInfo):
    authInfo = AUTH_INFO
    serverId = SERVER_ID
    ticketId = ticketInfo.TicketId
    wsdl = "http://13.231.65.63:8999/VPNAPIService.svc?wsdl"
    client = Client(wsdl)
    result = client.service.CompleteInstructionTicket(authInfo, ticketId, serverId)
    print('Updated')

# Send Mail to receiver
def SendMail(ticketInfo):
    print('...Sending...')
    subject = "VPN Key"
    body = "Thanks for choosing IT-Solution.\n***Automated email***"
    sender_email = "blackcoder.zed@gmail.com"
    receiver_email = ticketInfo.Email
    filename = HOME_DIR + ticketInfo.KeyName + '.txt'
    password = 'Password'
    attachName = ticketInfo.KeyName + '.txt'

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message["Bcc"] = receiver_email

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachName}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
    print('Send...')

def RegisterUser(ticketInfo):
    isExist = CheckExist(ticketInfo.KeyName)
    if isExist == True:
        print("Already existed")
        return False
    # generate password
    passwd = GenerateRandomPassword()
    ticketInfo.Password = passwd
    ipaddress = CalculateIP()
    # write to file
    with open('/etc/ppp/chap-secrets','a') as f:
        f.write('"'+ticketInfo.KeyName+'" l2tpd "' + passwd + '" ' + ipaddress + '\n')
    return True

def CheckExist(keyName):
    with open('/etc/ppp/chap-secrets','r') as f:
        logstr = f.read()
        if keyName in logstr:
            return True
        else:
            return False

def ExportToFile(ticketInfo):
    myfile = Path(HOME_DIR + ticketInfo.KeyName + '.txt')
    myfile.touch(exist_ok=True)
    with open(myfile, 'w') as f:
        textStr = "Type : L2TP/IPSec PSK" + '\n'
        textStr += "Server : " + SERVER_IP + '\n'
        textStr += "Pre-shared key : " + SECRET_KEY + '\n'
        textStr += "Username : " + ticketInfo.KeyName + '\n'
        textStr += "Password : " + ticketInfo.Password + '\n'
        f.write(textStr)

def GenerateRandomPassword():
    letters = string.ascii_lowercase
    randomStr = ''.join(random.choice(letters) for i in range(10));
    return randomStr

def GetCurrentIPList():
    ipList = []
    with open('/etc/ppp/chap-secrets','r') as f:
        lines = f.readlines()
        if '\n' in lines:
            lines.remove('\n')
        for line in lines:
            ip = line.split(" ")[3].replace("\n","")
            ipList.append(ip)
    return ipList
        

def CalculateIP():
    ipList = GetCurrentIPList()
    ipresult = ""
    for i in range(10, 100):
        calculatedIP = IP_Prefix + str(i)
        if calculatedIP not in ipList:
            ipresult = calculatedIP
            break;
    return ipresult
            

#########################################################################################
#                                  Entry Point                                          #
#########################################################################################
SERVER_ID = str(102)
SERVER_IP = ""
SECRET_KEY = ""
IP_Prefix = "192.168.42."
HOME_DIR = '/home/ubuntu/client/'
AUTH_INFO = {'UserID' : 'APIUser', 'Password' : '2019hacker'}
REQ_INFO = {'ServerID' : SERVER_ID, 'CommandCode' : 101}
StartOperation(SERVER_ID)
