import os
from suds.client import Client

#########################################################################################
#                                  KeyInfo Class                                        #
#########################################################################################

class KeyInfo:
    def __init__(self, TicketId, KeyName, Password, Email):
        self.TicketId = TicketId
        self.KeyName = KeyName
        self.Email = Email
        self.Password = Password

#########################################################################################
#                                  Methods                                              #
#########################################################################################
def DeleteClient(ServerID):
    ticketInfoLst = GetTicketInfo(ServerID)
    for ticketInfo in ticketInfoLst:
        # delete records
        DeleteRecord(ticketInfo.KeyName)

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
        

def UpdateTicketInfo(ticketInfo):
    authInfo = AUTH_INFO
    serverId = SERVER_ID
    ticketId = ticketInfo.TicketId
    wsdl = "http://13.231.65.63:8999/VPNAPIService.svc?wsdl"
    client = Client(wsdl)
    result = client.service.CompleteInstructionTicket(authInfo, ticketId, serverId)
    print('Updated')

def GetTicketInfo(serverId):
    authInfo = AUTH_INFO
    reqInfo = REQ_INFO
    ticketInfoLst = []
    wsdl = "http://localhost:65315/VPNAPIService.svc?WSDL"
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

#########################################################################################
#                                  Entry Point                                          #
#########################################################################################

SERVER_ID = str(121)
HOME_DIR = '/home/ubuntu/client/'
AUTH_INFO = {'UserID' : 'APIUser', 'Password' : '2019hacker'}
REQ_INFO = {'ServerID' : SERVER_ID, 'CommandCode' : 103}
DeleteClient(SERVER_ID)
