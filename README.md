# CZ1003-Telegram-Bot(ScrubzBot)

## Dependencies (Ext) - all via pip
- telepot
- BeautifulSoup4
- neverbounce_sdk
- sendgrid
- icalendar
- pytz

## Python libraries used
- time
- datetime
- base64
- urllib
- random
- threading

## Files

### validation.py
This python script contains two functions to syntatically verify a Matric Number as well as an email address. 

Function | Inputs | Return
--- | --- | ---
emailStaticCheck | user_email | True or False
matricNumberCheck | matricNumber | True or False


### sendemail.py: 
This python script handles the sending of email notifications and the generation of the iCalendar attachment.

Function | Inputs | Return
--- | --- | ---
genICal | data dictionary, module code, desired index number | formatted icalendar file, as bytes.
genHTMLMail | names and indexes of both parties, data dictionary, module code | email message body, as HTML
sendMails | name, index, email of both parties, data dictionary, module code | Nothing

Note: 
- data dictionary contains all the index and session details for the module. 
	{key: module index number, values: a series of Subj() objects, each representing one session (lec, tut, lab, etc) tagged to the index}
- For sendMails, it connects to sendgrid API and uses sendgrid's helper methods to construct a Mail() object, with the iCal and message body generated earlier. Then it sends the message and prints out the HTTP status code for monitoring. 


### NTUModSwap.py
This python script contains the main bot code.

Function | Remarks 
--- | ---
handle | Handles all the message objects received by telepot. 
callback | Handles all the callback queries received by telepot. We use this for subsequent navigation when the input is no longer free-form.
destroyUserSession | Helper method to end the session cleanly and remove a user's session variables.
listCurrent | Gets a user's current swaps from the CSV and output accordingly.
removeReg | Removes a user's registration and updates the CSV accordingly.
checkWaitList | Helper method to check the number of pending swaps for a particular index.
checkDuplicate | Helper method to check for duplicate entries by the same user.
matchSwapIndex | matching function. If match is found, send message via telegram [notifyUsers()] and trigger the email sending [sendemail.sendMails()]. Updates CSV thereafter.
notifyUsers | Notifies both parties of a successful swap. 
neverbounceVerify | Function that we call in a separate thread to do server-side email validation. Updates the session variable once done.
listOldIdx | Validates the module code input and calls [markupKeyboard()] to generate the inline buttons containing all indexes for the mod.
listNewIdx | Post-processes the old index data and calls [markupKeyboard()] again to generate the inline buttons sans the old index.
markupKeyboard | Generates for inline keyboard markup based on the data given and sends the message.
listModIdx | Displays all session data for a mod. Wraps around the [listModDataAsText()] function to actually send the message and provide input validation.
listModDataAsText | Takes in a data dictionary and returns a stringified representation of all its indexes and sessions.
dataScrape | Base Scraping function. a Subj() object is created for each session and these are inserted into a dictionary with the index number as the key. 
class Subj | Base definition for the Subj() object. has one helper method .preview() to generate a string representation of the object's data. 


Note:
For *handle*, we distinguish using a step counter:
- 2.0: has /start-ed, at main memu
- 	/1: User wants to view module indexes. Ask for first input (mod code entry). We increment the step counter to 2.1 here to stream his next input (module code).
- 	/2: User wants to swap. Ask for first input (matric entry). Set step counter to 2.2 to stream the next input (matric number) to the correct next step (validation).
- 	/3: User wants to view. Generate list and output. End session.
- 	/4: User wants to delete. Generate list and output, and ask for input (# to delete). We set the step counter to 2.5 here to stream his next input (# for deletion).
- 2.1: Takes in the input (mod code) and retrieves the data [listModIdx()].
- 2.2: Takes in the input (matric) and validates it. If valid, store it and ask for second input (email entry). Increment step counter to 2.3 to stream the next input (email) to the correct next step (validation).
- 2.3: Takes in the input (email) and validates it. If valid, store it and ask for third input (mod code). Increment step counter to 2.4 to stream the next input (mod code) to the correct next step (transition to callback button interface).
- 2.4: Takes in the input (mod code) and transitions to the callback button based interface. [listOldIdx()]
- 2.5: Takes in the input (index to be deleted) and processes deletion. End session.

For *callback* , we distinguish the steps here using the query data.
- 'old': user has sent in his old index. Collapse the buttons, store it, and output a new selection sans the old index [listNewIdx()].
- 'new': user has sent in his new index. Collapse the buttons, store it, check for result from server side email validation, and insert into db and run the matching script if rmail is valid. [matchSwapIndex()] End session.
- 'mod': user wants to view module data. We transplant the function from step 2.1 above here and output accordingly. [listModDataAsText()]
- 'del': destroys the message sent via 'mod' above. 

## Setup
Bot is currently running on an AWS instance running ubuntu 16.04. We used `screen` to run the python script on a detached screen such that exiting the SSH session won't terminate the bot.
