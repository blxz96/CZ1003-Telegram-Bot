import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

import time
import urllib
import urllib.request
import csv
import random
import threading

import neverbounce_sdk
from bs4 import BeautifulSoup

import validation
import sendemail

#dicts to store data of all active users
activeUserStep = {}
activeUserMod = {}
activeUserMatriNo = {}
activeUserEmail = {}
activeUserOldIdx = {}
activeUserNewIdx = {}
activeUserModData = {}
activeUserEmailCheck = {}

threads = [] #thread
stickers = ["CAADBQADWwEAAnqYVQOmAwXO7IIhKwI", "CAADBQADJRMAArCYGwEh5ySnPuTfvwI", "CAADBQAD6QADbqRAAjejGqxc_D6QAg"]

def handle(msg):
    #Extracting telegram user's infromation
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)
    try:
        command = msg['text']
        print(command)
    except:
        bot.sendSticker(chat_id, "CAADBQAD2AADbqRAAkRVY9vVk6IfAg")
        bot.sendMessage(chat_id, "This bot only accepts text as inputs!")
        command = ""
    print(activeUserStep)

    #Initialize variables of the specific user if existing variables are not initialize
    if not chat_id in activeUserStep:
        activeUserStep[chat_id] = 0.0
        activeUserMatriNo[chat_id] = None
        activeUserEmail[chat_id] = None
        activeUserMod[chat_id] = None
        activeUserOldIdx[chat_id] = None
        activeUserNewIdx[chat_id] = None
        activeUserModData[chat_id] = None
        activeUserEmailCheck[chat_id] = None

    #List table of commands
    if command == "/start":
        sendMsg = "**Welcome to NTU Module Index Swapping Bot.**\n" \
                  "[/1]. List Module Indexes and details\n""" \
                  "[/2]. Register for Index Swapping\n" \
                  "[/3]. View your current Index Swapping status\n" \
                  "[/4]. Cancel registered Index Swapping\n" \
                  "[/quit]. Quit"

        bot.sendMessage(chat_id,sendMsg)
        activeUserStep[chat_id] = 2.0

    #Quit bot
    elif command == "/quit":
        #Discard all existing data specific to the user
        destroyUserSession(chat_id)
        print(activeUserStep)

    #Capture Course Code
    elif activeUserStep[chat_id] == 2.0 and command == "/1":
        sendMsg = 'Please input your Course Code (E.g. CZ1003)'
        bot.sendMessage(chat_id, sendMsg)
        activeUserStep[chat_id] = 2.1

    #List Module Indexes and details
    elif activeUserStep[chat_id] == 2.1:
        listModIdx(command,chat_id)

    #Capture user Matriculation Number
    elif activeUserStep[chat_id] == 2.0 and command == "/2":
        sendMsg = 'Please input your Matriculation Number'
        bot.sendMessage(chat_id, sendMsg)
        activeUserStep[chat_id] = 2.2

    #Validate Matric and Capture user Email
    elif activeUserStep[chat_id] == 2.2:
        try:
            #Validate User Matric Number
            if validation.matricNumberCheck(command) == False: raise ValueError()
            #otherwise, store the matric number
            activeUserMatriNo[chat_id] = command
            #ask for email
            sendMsg = "Please input your preferred Email address:\n [Please use NTU or gmail addresses as hotmail\'s overzealous filters like to redirect our messages to the Junk folder :(]"
            bot.sendMessage(chat_id, sendMsg)
            activeUserStep[chat_id] = 2.3
        except:
            bot.sendMessage(chat_id, "Invalid Matric Number! Please try again.")

    #Validate email and Capture user course code
    elif activeUserStep[chat_id] == 2.3:
        try:
            #client side syntax check
            if validation.emailStaticCheck(command) == False: raise ValueError()
            #cancerous bit - run API call as thread
            t = threading.Thread(target=neverbounceVerify, args=(command, chat_id))
            threads.append(t)
            t.start()
            #Store User Email first - catch bad emails once more later
            activeUserEmail[chat_id] = command
            sendMsg = 'Please input your Course Code (E.g. CZ1003)'
            bot.sendMessage(chat_id, sendMsg)
            activeUserStep[chat_id] = 2.4
        except:
            bot.sendMessage(chat_id, "Invalid email address! please try again.")

    #Output a list of indexes as inline buttons. rest of swapping process is handled by callback button handler
    elif activeUserStep[chat_id] == 2.4:
        listOldIdx(command,chat_id)

    #List user current Index Swapping status
    elif activeUserStep[chat_id] == 2.0 and command == "/3":
        sendMsg = listCurrent(chat_id, False)
        if sendMsg != "":
            bot.sendMessage(chat_id, sendMsg)
        destroyUserSession(chat_id) # kill the session regardless since we're just displaying

    #List user current Index Swapping status + prompt user which one they will like to remove
    elif activeUserStep[chat_id] == 2.0 and command == "/4":
        activeUserStep[chat_id] = 2.5
        sendMsg = listCurrent(chat_id, True)
        if sendMsg=="": #nothing is returned i.e. user has no swaps
            destroyUserSession(chat_id)
        else:
            bot.sendMessage(chat_id, sendMsg)

    #Remove registration
    elif activeUserStep[chat_id] == 2.5:
        removeReg(command,chat_id)

    #Notify user of wrong input
    else:
        bot.sendMessage(chat_id,"Wrong Input!")

def callback(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    # for private chats, from_id == chat_id

    print('Callback Query:', query_id, from_id, query_data)
    query_data = query_data.split(";")

    if query_data[0] == 'old':  # user has selected old index
        bot.editMessageText(telepot.message_identifier(msg['message']),
                            "You have selected Index no. " + query_data[1])
        activeUserOldIdx[from_id] = query_data[1]
        listNewIdx(query_data[1], from_id)

    elif query_data[0] == 'new':  # user has selected new index
        bot.editMessageText(telepot.message_identifier(msg['message']),
                            "You have selected Index no. " + query_data[1] + " to swap into.")
        activeUserNewIdx[from_id] = query_data[1]
        bot.sendMessage(from_id, "Processing...")
        # if email is still validating (I hope not), we stall
        threads[0].join()
        if activeUserEmailCheck[from_id] == False:
            bot.sendMessage(from_id, "Naughty naughty! Further validation has found that your email " + \
                            "address is in fact invalid. This bot will now quit.")
            bot.sendSticker(from_id, "CAADBQADzgADbqRAAn_r6fO8RQf7Ag")
        else:
            sendMsg = "Your request has been entered into our database." + \
                      ".\nWe will notify you once we have found you a match."
            bot.sendSticker(from_id, stickers[random.randrange(0, 3)])
            bot.sendMessage(from_id, sendMsg)
            # database Insert Data
            matchSwapIndex(from_id)
        # Destroy User Session
        destroyUserSession(from_id)

    elif query_data[0] == 'mod':  # user wants to see session details
        sendMsg = listModDataAsText(activeUserModData[from_id])
        inline_kb = [
            [(InlineKeyboardButton(text="Done? Click here to collapse this message", callback_data="del;0"))]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=inline_kb)
        bot.sendMessage(from_id, sendMsg, 'markdown', reply_markup=keyboard)

    elif query_data[0] == 'del':  # session details message is collapsible
        bot.deleteMessage(telepot.message_identifier(msg['message']))

    bot.answerCallbackQuery(query_id)

#Discard all existing data specific to the user
def destroyUserSession(chat_id):
    bot.sendMessage(chat_id, "Thanks for using this Bot. To start the Bot again input /start.\nHave a nice day =D")
    del activeUserStep[chat_id]
    del activeUserOldIdx[chat_id]
    del activeUserNewIdx[chat_id]
    del activeUserMod[chat_id]
    del activeUserMatriNo[chat_id]
    del activeUserEmail[chat_id]
    del activeUserModData[chat_id]
    del activeUserEmailCheck[chat_id]

#List user current Index Swapping status
def listCurrent(chat_id, commandRemove_bool):
    #Open and read csv file
    with open('NTUModSwap.csv', 'r') as fp:
        reader = csv.reader(fp)
        data = list(reader)

    listCurrentStr = ""
    #Count the total number of unique registration by the user
    count = 0

    #Make Serial number a /command if user selected Option 4 (/4).
    if commandRemove_bool:
        commandRemoveStr = "/"
    else:
        commandRemoveStr = ""

    for i in range(1,len(data)):
        #Extarct registration information if tuple from data[] is registered by user and it is not matched.
        if str(chat_id) == data[i][0] and data[i][6] == "False":
            #Calculate user waiting list queue
            waitQueue = checkWaitList(data,data[i][4], i)
            listCurrentStr +=  commandRemoveStr +str(count+1) + " ========\n"\
                              "MOD CODE: " + data[i][3] +\
                             "\nCURRENT INDEX: " + data[i][4] +\
                             "\nPREFERRED INDEX: " + data[i][5] +\
                             "\nYour Current Waitlist Queue: " + str(waitQueue) + "\n\n"
            count += 1

    #Output string if user selected Option 4 (/4).
    if commandRemove_bool:
        listCurrentStr += "==========\n" \
                          "Input /<Serial Number> (E.g. /1 ) to remove your desired registration."

    # Output string if there is 0 unique registration by the user. We send the message here
    # as we want an easy way (an empty return value) to distinguish the 'no swaps' case
    if count == 0:
        listCurrentStr = ""
        bot.sendMessage(chat_id,"You do not have any Index Swap registered.")

    return listCurrentStr

#Remove registration by serial number
def removeReg(serialNo_Str, chat_id):
    # Open and read csv file
    with open('NTUModSwap.csv', 'r') as fp:
        reader = csv.reader(fp)
        data = list(reader)

    #True if removal is successful. Else False.
    successful_bool = False
    try:
        #Casting command input (E.g. /1) into int (E.g. 1)
        serialNo_int = int(serialNo_Str[1:])
        count = 1
        for i in range(1, len(data)):
            #Delete tuple if tuple correspond to serial number specified by user
            if str(chat_id) == data[i][0] and data[i][6] == "False":
                if count == serialNo_int:
                    del data[i]
                    successful_bool = True
                    break
                count += 1

        #Insert modified list into csv if removal is successful
        if successful_bool:
            with open("NTUModSwap.csv", "w", newline="") as fp:
                db = csv.writer(fp, delimiter=",")
                db.writerows(data)

            #List new current registration by the user
            sendMsg = listCurrent(chat_id, False)
            sendMsg += "Removal is successful!"
            bot.sendMessage(chat_id, sendMsg)
            # Discard all existing data specific to the user
            destroyUserSession(chat_id)
        #Output string if there is no removal
        else:
            sendMsg = "Serial Number not found!"
            bot.sendMessage(chat_id, sendMsg)
    #Output string action could not be executed due to invalid command
    except:
        sendMsg = "You have entered an invalid command!"
        bot.sendMessage(chat_id, sendMsg)

#Check and return the wait list queue
def checkWaitList(data,oldIdx, currentPosition):
    waitQueue = 1
    for i in range(1,currentPosition):
        if oldIdx == data[i][4] and data[i][6] == "False":
            waitQueue += 1

    return waitQueue

#Check for duplication entry by the same user
def checkDuplicate(chat_id, data ,newIdx,oldIdx):
    isDuplicate = False #True if there is duplicate, else False
    for i in range(1,len(data)):
        if str(chat_id) == data[i][0] and newIdx == data[i][5] and oldIdx == data[i][4] and data[i][6] == "False":
            isDuplicate = True
            break
    return isDuplicate

#Compare current Index and Preferred Index in our database
def matchSwapIndex(chat_id):
    #Open and read csv file
    with open('NTUModSwap.csv', 'r') as fp:
        reader = csv.reader(fp)
        data = list(reader)

    #True if there is a Match for user to swap with. Else False
    isMatch = False
    match_chat_id = ""

    # True if there is duplicate, else False
    isDuplicate = checkDuplicate(chat_id, data ,activeUserNewIdx[chat_id],activeUserOldIdx[chat_id])

    if isDuplicate == False:
        for i in range(1,len(data)):
            #Compare active user current index and preferred index for every tuple
            if data[i][6] == "False" and activeUserNewIdx[chat_id] == data[i][4] and activeUserOldIdx[chat_id] == data[i][5]:
                match_chat_id = data[i][0]
                #Notify User they have a match
                notifyUsers(chat_id, match_chat_id)
                # Send email to notify User
                try:
                    sendemail.sendMails(bot.getChat(chat_id)['first_name'], activeUserOldIdx[chat_id], activeUserEmail[chat_id], \
                                    bot.getChat(match_chat_id)['first_name'], activeUserNewIdx[chat_id], data[i][2], \
                                    activeUserModData[chat_id], data[i][3])
                except:
                    print("Email sending error!")
                #Updating database
                data[i][6] = True
                #Update Match_Id
                data[i][7] = str(chat_id)
                isMatch = True
                break
        #Append new tuple
        with open("NTUModSwap.csv", "w", newline="") as fp:
            db = csv.writer(fp, delimiter=",")
            store_chat_id = str(chat_id)
            store_Mod = str(activeUserMod[chat_id])
            store_MatriNo = str(activeUserMatriNo[chat_id]).upper()
            store_email = str(activeUserEmail[chat_id]).upper()
            store_OldIdx = str(activeUserOldIdx[chat_id])
            store_isMatch = str(isMatch)
            store_NewIdx = str(activeUserNewIdx[chat_id])
            data.append([store_chat_id, store_MatriNo, store_email, store_Mod, store_OldIdx, store_NewIdx,store_isMatch,match_chat_id])
            db.writerows(data)

#Notify user of their successful outcomes
def notifyUsers(chat_id_user1, chat_id_user2):
    name_user1 = bot.getChat(chat_id_user1)['first_name']
    name_user2 = bot.getChat(chat_id_user2)['first_name']
    sendMsgUser1 = "<a href='tg://user?id=" + str(chat_id_user2) + "'>" + name_user2 + "</a> would like to swap INDEX <b>" + activeUserNewIdx[chat_id_user1] +\
                   "</b> with your INDEX <b>" + activeUserOldIdx[chat_id_user1] + "</b> for the Module " + activeUserMod[chat_id_user1] + ". Click on his name above to chat!"

    sendMsgUser2 = "<a href='tg://user?id=" + str(chat_id_user1) + "'>" + name_user1 + "</a> would like to swap INDEX <b>" + activeUserOldIdx[chat_id_user1] + \
                   "</b> with your INDEX <b>" + activeUserNewIdx[chat_id_user1] + "</b> for the Module " + activeUserMod[chat_id_user1] + ". Click on his name above to chat!"

    bot.sendMessage(chat_id_user1, sendMsgUser1, 'html')
    bot.sendMessage(chat_id_user2, sendMsgUser2, 'html')

#server-side email verification
def neverbounceVerify(add, chat_id):
    api_key = 'secret_e3eb4f28f87667fb9b6bea7b73e5e9d0'
    client = neverbounce_sdk.client(api_key=api_key)
    resp = client.single_check(email=add, timeout=7)
    if resp['result'] == "invalid" or resp['result'] == "disposable":
        activeUserEmailCheck[chat_id] = False
    elif resp['result'] == "valid" or resp['result'] == "catchall" or resp['result'] == "unknown":
        activeUserEmailCheck[chat_id] = True
    print("Neverbounce result", resp['result'], activeUserEmailCheck[chat_id])
    print(activeUserEmailCheck)
    return

#Output a list of indexes (minus current Index) as inline buttons
def listNewIdx(oldIdx, chat_id):
    try:
        modIdx = list(activeUserModData[chat_id].keys())
        modIdx.remove(oldIdx)
        sendMsg = "Select the new INDEX you wish to swap with"
        markUpKeyboard(modIdx, chat_id, sendMsg, "new")

    except:
        bot.sendMessage(chat_id, "Wrong INDEX Code!")

#Output a list of indexes as inline buttons
def listOldIdx(modCode,chat_id):
    try:
        if len(modCode) == 6:
            activeUserModData[chat_id] = dataScrape(modCode)
            modIdx = list(activeUserModData[chat_id].keys())
            if(len(modIdx)==1):
                sendMsg = 'This module only has one index! what are you trying to do?!'
                bot.sendMessage(chat_id, sendMsg)
                bot.sendSticker(chat_id, "CAADBQADzgADbqRAAn_r6fO8RQf7Ag")
                destroyUserSession(chat_id)
            else:
                sendMsg ='What is your current Index for ' + modCode + '?'''
                markUpKeyboard(modIdx, chat_id, sendMsg, "old", modCode)
                activeUserMod[chat_id] = modCode.upper()
        else:
            bot.sendMessage(chat_id, "Wrong Module Code!")
    except:
        bot.sendMessage(chat_id, "Wrong Module Code!")

#Inline Keyboard
def markUpKeyboard(choiceList, chat_id, sendMsg, prefix, modCode="0"):
    inline_kb = []
    temp = [] #row of buttons
    if(modCode!="0" and prefix=="old"):
        inline_kb.append([(InlineKeyboardButton(text="Unsure? Click to view class schedules", callback_data="mod;0"))])
    for i in range(0,len(choiceList)):
        if i%4 == 0:
            temp=[]
            temp.append(InlineKeyboardButton(text=choiceList[i], callback_data=prefix+";"+choiceList[i]))
        elif i%4 == 3 or i == len(choiceList)-1: #4 buttons in 1 row, or last row
            temp.append(InlineKeyboardButton(text=choiceList[i], callback_data=prefix+";"+choiceList[i]))
            inline_kb.append(temp)
        else:
            temp.append(InlineKeyboardButton(text=choiceList[i], callback_data=prefix+";"+choiceList[i]))

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    bot.sendMessage(chat_id, sendMsg, reply_markup=keyboard)

#List Module Indexes and details - ONLY
#not passing in `data` here as there's no point in storing when the user just wants to see and that's it
def listModIdx(modCode, chat_id):
    try:
        if len(modCode) == 6:
            data = dataScrape(modCode)
            bot.sendMessage(chat_id, listModDataAsText(data), 'markdown')
            destroyUserSession(chat_id)
        else:
            bot.sendMessage(chat_id, "Wrong Module Code!")
    except:
        bot.sendMessage(chat_id, "Wrong Module Code!")

def listModDataAsText(data):
    sendMsg = ""
    for idx in data.keys():
        sendMsg += "*" + str(idx) + ":*\n"
        for subj in data[idx]:
            sendMsg += subj.preview() + "\n"
    return sendMsg

def dataScrape(modCode):
    url = 'https://wish.wis.ntu.edu.sg/webexe/owa/AUS_SCHEDULE.main_display1'

    values = {'acadsem': '2017;1',
              'r_course_yr': '',
              'r_subj_code': modCode,
              'r_search_type': 'F',
              'boption': 'Search',
              'staff_access': 'false'}
    headers = {'Host': 'wish.wis.ntu.edu.sg',
               'Referer': 'https://wish.wis.ntu.edu.sg/webexe/owa/aus_schedule.main',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Connection': 'keep-alive',
               'Upgrade-Insecure-Requests': '1',
               'Pragma': 'no-cache',
               'Cache-Control': 'no-cache'}
    print("Scraping for", modCode)
    data = urllib.parse.urlencode(values).encode('ascii')
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
    soup = BeautifulSoup(the_page, "html5lib")

    # gets second table (first table is for the course title and prereqs)
    # and throws away the first row (column headers) => gives us the raw data we need
    # this will throw an error if module code is invalid as the schedules table won't exist
    res = soup.find_all("table")[1].find_all('tr')[1:]
    data = {}

    # processing the html. Subj() object contains the details for 1 session [lec/tut/lab/etc]
    for row in res:
        elems = row.find_all('td')
        if (row.td.b.text != ""):  # first column in the row (index number col)
            temp = row.td.b.text  # gets the index number - we store it as we want it to remain constant as we associate the next rows (tuts/labs) with the index
            data[temp] = []
            subj = Subj(elems[1].b.text, elems[2].b.text, elems[3].b.text, elems[4].b.text, elems[5].b.text)
            data[temp].append(subj)
        else:
            subj = Subj(elems[1].b.text, elems[2].b.text, elems[3].b.text, elems[4].b.text, elems[5].b.text)
            data[temp].append(subj)
    return data

class Subj:
    def __init__(self, initType, initGrp, initDay, initTime, initLoc):
        self.type = initType
        self.group = initGrp
        self.day = initDay
        self.time = initTime
        self.loc = initLoc
    def preview(self):
        return self.type[:3] + " (" + self.group + ") on " + self.day + " at " + self.time


bot = telepot.Bot("330337414:AAFRnDvcZ4ZW9j7ww-yuKRMFElHkR4VYgX0")
MessageLoop(bot, {'chat': handle,
                  'callback_query': callback}).run_as_thread()
print('Listening')

while True:
    time.sleep(10)
