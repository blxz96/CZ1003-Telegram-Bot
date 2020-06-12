import sendgrid
from sendgrid.helpers.mail import *
import icalendar
import pytz
import time
from datetime import datetime
from datetime import timedelta
import base64

#start of sem = wk1 monday, end = wk13 sat
semStart = datetime(2017, 8, 14, 0, 0, 0, tzinfo=pytz.utc)
recess = datetime(2017, 10, 2, 0, 0, 0, tzinfo=pytz.utc)
semEnd = datetime(2017, 11, 18, 0, 0, 0, tzinfo=pytz.utc)

#takes the base value (14 Aug 0:00) and transforms it into the lesson time
def transformTime(day, hr, minute, init=semStart):
    dt = init + timedelta(days=time.strptime(day, '%a').tm_wday)
    dt += timedelta(hours=hr-8) #GMT makes life much easier
    dt += timedelta(minutes=minute)
    return dt

def genICal(data, modCode, index):
    cal = icalendar.Calendar()
    cal.add('prodid', '-//NTUmodswap bot//')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')

    for i in data[index]:
        event = icalendar.Event()
        event.add('summary', modCode + " " + i.type)
        event.add('location', i.loc)
        if i.type=="TUT":
            event.add('dtstart', timedelta(days=7) + transformTime(i.day, int(i.time[0:2]), int(i.time[2:4])))
            event.add('dtend', timedelta(days=7) + transformTime(i.day, int(i.time[5:7]), int(i.time[7:9])))
        else:
            event.add('dtstart', transformTime(i.day, int(i.time[0:2]), int(i.time[2:4])))
            event.add('dtend', transformTime(i.day, int(i.time[5:7]), int(i.time[7:9])))
        event.add('dtstamp', datetime.now())
        event.add('rrule', icalendar.vRecur({"FREQ":"WEEKLY", "UNTIL": semEnd}))
        event.add('exdate', transformTime(i.day, int(i.time[0:2]), int(i.time[2:4]), recess))
        cal.add_component(event)

    # print(str(cal.to_ical()))
    return cal.to_ical()

def sendMails (user1_name, user1_index, user1_email, user2_name, user2_index, user2_email, data, modCode):
    sg = sendgrid.SendGridAPIClient(apikey='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')

    mail = Mail()
    mail.from_email = Email("NTUmodswap@hotmail.com", "NTU Module Swapper")
    mail.subject = "Swap Found!"
    personalization = Personalization()
    personalization.add_to(Email(user1_email, "User"))
    personalization.subject = "Swap Found!"
    mail.add_personalization(personalization)

    mail.add_content(Content("text/html", genHTMLMail(user1_name, user1_index, user2_name, user2_index, data, modCode)))

    attachment = Attachment()
    attachment.content = base64.b64encode(genICal(data, modCode, user2_index)).decode()
    attachment.type = "application/ics"
    attachment.filename = "event.ics"
    attachment.disposition = "attachment"
    attachment.content_id = "cal"
    mail.add_attachment(attachment)

    response = sg.client.mail.send.post(request_body=mail.get())
    print("Email", response.status_code, user1_email)
    #print(response.body)
    #print(response.headers)

    mail2 = Mail()
    mail2.from_email = Email("NTUmodswap@hotmail.com", "NTU Module Swapper")
    mail2.subject = "Swap Found!"
    personalization2 = Personalization()
    personalization2.add_to(Email(user2_email, "User"))
    personalization2.subject = "Swap Found!"
    mail2.add_personalization(personalization2)

    mail2.add_content(Content("text/html", genHTMLMail(user2_name, user2_index, user1_name, user1_index, data, modCode)))

    attachment2 = Attachment()
    attachment2.content = base64.b64encode(genICal(data, modCode, user1_index)).decode()
    attachment2.type = "application/ics"
    attachment2.filename = "event.ics"
    attachment2.disposition = "attachment"
    attachment2.content_id = "cal2"
    mail2.add_attachment(attachment2)

    response = sg.client.mail.send.post(request_body=mail2.get())
    print("Email", response.status_code, user2_email)
    #print(response.body)
    #print(response.headers)

    return

def genHTMLMail(user1_name, user1_index, user2_name, user2_index, data, modCode):
    mailStr = "<html><body>Hi there <b>" + user1_name + "</b>,<br/><br/>" + \
              "<b>" + user2_name + "</b> wants to swap index numbers with you for mod " + modCode + \
              "!<br/><br/><table><tr><th colspan='5'><b>Old</b></th><th colspan='5'><b>New</b></th>" + \
              "<tr><td rowspan='" + str(len(data[user1_index])) + "'>" + user1_index + "</td><td>" + \
              data[user1_index][0].type + "</td><td>" + data[user1_index][0].group + "</td><td>" + \
              data[user1_index][0].day + " " + data[user1_index][0].time + "</td><td>" + \
              data[user1_index][0].loc + "</td><td rowspan='" + str(len(data[user2_index])) + "'>" + \
              user2_index + "</td><td>" + data[user2_index][0].type + "</td><td>" + \
              data[user1_index][0].group + "</td><td>" + data[user1_index][0].day + " " + \
              data[user1_index][0].time + "</td><td>" + data[user1_index][0].loc + "</td></tr>"

    for i in range(1, len(data[user1_index])):
        mailStr += "<tr><td>" + data[user1_index][i].type + "</td><td>" + \
                   data[user1_index][i].group + "</td><td>" + data[user1_index][i].day + " " + \
                   data[user1_index][i].time + "</td><td>" + data[user1_index][i].loc + "</td><td>" + \
                   data[user2_index][i].type + "</td><td>" + data[user2_index][i].group + "</td><td>" + \
                   data[user2_index][i].day + " " + data[user2_index][i].time + "</td><td>" + data[user2_index][
                       i].loc + "</td></tr>"

    mailStr += "</table><br/><br/>Open the NTU Mod Swap chat to connect!" + \
               "<br/><br/>Do open the attached file to add your new index details to your calendar!<br/><br/>" + \
               "Thanks for using NTUmodswap!</body></html>"
    return mailStr
