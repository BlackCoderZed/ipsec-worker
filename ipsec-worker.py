from suds.client import Client
from xml.dom import minidom
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
#                                  Config Class                                         #
#########################################################################################

class Configuration:
    def __init__(self, ServerId, ServerIP, SecretKey, EmailAddress, Password, SmtpServer, IpPrefix, SaveDir, ApiUrl):
        self.ServerId = ServerId
        self.ServerIP = ServerIP
        self.SecretKey = SecretKey
        self.EmailAddress = EmailAddress
        self.Password = Password
        self.SmtpServer = SmtpServer
        self.IpPrefix = IpPrefix
        self.SaveDir = SaveDir
        self.ApiUrl = ApiUrl

    def LoadConfiguration():
        filedir = os.path.dirname(os.path.realpath(__file__))
        doc = minidom.parse(filedir+"/config.xml")
        config = doc.getElementsByTagName("config")[0]
        serverId = config.getElementsByTagName("ServerId")[0].firstChild.data
        serverIP = config.getElementsByTagName("ServerIP")[0].firstChild.data
        secretKey = config.getElementsByTagName("SecretKey")[0].firstChild.data
        emailAddress = config.getElementsByTagName("EmailAddress")[0].firstChild.data
        password = config.getElementsByTagName("Password")[0].firstChild.data
        smtpAddress = config.getElementsByTagName("SmtpAddress")[0].firstChild.data
        ipPrefix = config.getElementsByTagName("IpPrefix")[0].firstChild.data
        saveDir = config.getElementsByTagName("SaveDir")[0].firstChild.data
        apiUrl = config.getElementsByTagName("APIUrl")[0].firstChild.data
        config = Configuration(serverId, serverIP, secretKey, emailAddress, password, smtpAddress, ipPrefix, saveDir, apiUrl)
        return config

#########################################################################################
#                                  KeyInfo Class                                        #
#########################################################################################

class KeyInfo:
    def __init__(self, TicketId, KeyName, Password, Email):
        self.TicketId = TicketId
        self.KeyName = KeyName
        self.Email = Email
        self.Password = Password


def StartRegistrationProcess():
    ticketInfoList = GetTicketInfo(REGISTER_REQ_INFO)
    for ticketInfo in ticketInfoList:
        isSuccess = RegisterUser(ticketInfo)
        if (isSuccess == True):
            print("User Registeration success")
            conf_path = ExportToFile(ticketInfo)
            UpdateTicketInfo(ticketInfo)
            SendKey(ticketInfo, conf_path)

def StartDeleteProcess():
    ticketInfoLst = GetTicketInfo(DELETE_REQ_INFO)
    for ticketInfo in ticketInfoLst:
        # delete records
        DeleteRecord(ticketInfo.KeyName)
        UpdateTicketInfo(ticketInfo)

def DeleteRecord(username):
    print('Deleting...')
    lines = []
    with open('/etc/ppp/chap-secrets','r') as f:
        lines = f.readlines()
        for line in lines:
            if username in line:
                lines.remove(line)
    with open('/etc/ppp/chap-secrets','w') as f:
        f.writelines(lines)

# Get Instruction List
def GetTicketInfo(requestInfo):
    authInfo = AUTH_INFO
    reqInfo = requestInfo
    ticketInfoLst = []
    wsdl = API_URL
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
    wsdl = API_URL
    client = Client(wsdl)
    result = client.service.CompleteInstructionTicket(authInfo, ticketId, serverId)
    print('Updated')

def ReadConfig(conf_path):
    with open(conf_path, "r", encoding="utf-8") as f:
        return f.read()

def SendKey(ticketInfo, conf_path):
    print("Sending to API...")

    keycontent_conf = ReadConfig(conf_path)
    #keycontent_qr = ReadFileAsBase64(qr_path)

    keyname_conf = os.path.basename(conf_path)
    #keyname_qr = os.path.splitext(keyname_conf)[0] + ".png"

    client = Client(API_URL)

    # Create main SOAP request
    req = client.factory.create("ns1:ReqMultiSendKeyInfo")
    req.Email = ticketInfo.Email
    req.ServerID = SERVER_ID
    req.Subject = "L2TP by IT-Solution"

    # Create SOAP array of files
    req.KeyFiles = client.factory.create("ns1:ArrayOfKeyFileInfo")
    req.KeyFiles.KeyFileInfo = []

    # ---------- 1) CONF FILE ----------
    kf_conf = client.factory.create("ns1:KeyFileInfo")
    kf_conf.KeyContent = keycontent_conf
    kf_conf.KeyName = keyname_conf
    kf_conf.MediaType = "text/plain"
    req.KeyFiles.KeyFileInfo.append(kf_conf)

    # ---------- 2) QR PNG FILE ----------
    #kf_qr = client.factory.create("ns1:KeyFileInfo")
    #kf_qr.KeyContent = keycontent_qr
    #kf_qr.KeyName = keyname_qr
    #kf_qr.MediaType = "image/png"
    #req.KeyFiles.KeyFileInfo.append(kf_qr)

    # Call API
    client.service.SendMultipleKey(AUTH_INFO, req)

    print("Complete...")



# Send Mail to receiver
def SendMail(ticketInfo):
    print('...Sending...')
    subject = "VPN Key"
    body = "Thanks for choosing IT-Solution.\n***Automated email***"
    sender_email = EMAIL_ADDRESS
    receiver_email = ticketInfo.Email
    filename = HOME_DIR + ticketInfo.KeyName + '.txt'
    password = EMAIL_PASSWORD
    attachName = ticketInfo.KeyName + '.txt'

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = EMAIL_ADDRESS
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
    with smtplib.SMTP(SMTP_ADDRESS, 587) as server:
        server.starttls(context=context)
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
    isExist = False
    with open('/etc/ppp/chap-secrets','r') as f:
        logstr = f.read()
        if keyName in logstr:
            isExist = True
        else:
            isExist = False
    return isExist

def ExportToFile(ticketInfo):
    file_path = os.path.join(HOME_DIR, ticketInfo.KeyName + ".txt")
    myfile = Path(file_path)
    myfile.touch(exist_ok=True)
    with open(myfile, 'w') as f:
        textStr = "Type : L2TP/IPSec PSK" + '\n'
        textStr += "Server : " + SERVER_IP + '\n'
        textStr += "Secret : " + SECRET_KEY + '\n'
        textStr += "Account : " + ticketInfo.KeyName + '\n'
        textStr += "Password : " + ticketInfo.Password + '\n'
        f.write(textStr)
    return file_path

def GenerateRandomPassword():
    letters = string.ascii_lowercase + string.ascii_uppercase + str(1234567890)
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
config = Configuration.LoadConfiguration()
SERVER_ID = config.ServerId
SERVER_IP = config.ServerIP
SECRET_KEY = config.SecretKey
EMAIL_ADDRESS = config.EmailAddress
EMAIL_PASSWORD = config.Password
SMTP_ADDRESS = config.SmtpServer
IP_Prefix = config.IpPrefix
HOME_DIR = config.SaveDir
API_URL = config.ApiUrl
AUTH_INFO = {'UserID' : 'APIUser', 'Password' : '2017hacker'}
REGISTER_REQ_INFO = {'ServerID' : SERVER_ID, 'CommandCode' : 101}
DELETE_REQ_INFO = {'ServerID' : SERVER_ID, 'CommandCode' : 103}
StartRegistrationProcess()
StartDeleteProcess()
