import pyodbc
import os

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
    server = 'tcp:13.231.65.63' 
    database = 'It-Solution-OpenVPN' 
    username = 'sa' 
    password = 'Superm@n' 
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()

    query = "update Instructions Set InstructionStatusID = 2 where TicketID = "+ str(ticketInfo.TicketId) +";"
    cursor.execute(query)
    cursor.commit()
    cursor.close()
    cnxn.close()
    print('Updated')

def GetTicketInfo(serverId):
    ticketInfoLst = []
    server = 'tcp:13.231.65.63' 
    database = 'It-Solution-OpenVPN' 
    username = 'sa' 
    password = 'Superm@n' 
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = cnxn.cursor()

    query = """select Inst.TicketID,Inst.CommandCode,KeyInfo.Name as [KeyName],Cust.EmailAddress as [Emai] from Instructions as Inst
        inner join KeyInformations as KeyInfo on Inst.KeyInfoId = KeyInfo.Id inner join Customers as Cust on KeyInfo.CustomerID = Cust.CustomerId 
        where Inst.CommandCode = 103 and Inst.InstructionStatusID = 1 and Inst.ServerID = """+serverId+""";"""


    cursor.execute(query)
    resultLst = cursor.fetchall()

    for result in resultLst:
        ticketId = result[0]
        keyName = result[2]
        email = result[3]
        kInfo = KeyInfo(ticketId, keyName, '', email)
        ticketInfoLst.append(kInfo)
    cursor.close()
    cnxn.close()

    return ticketInfoLst

#########################################################################################
#                                  Entry Point                                          #
#########################################################################################

SERVER_ID = str(121)
HOME_DIR = '/home/ubuntu/client/'
DeleteClient(SERVER_ID)
