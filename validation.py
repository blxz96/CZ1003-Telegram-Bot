import string

def emailStaticCheck(user_email):
    # The format of email addresses is local-part@domain
    # local part may be up to 64 characters long
    # domain may have a maximum of 255 characters
    # but the maximum of 256-character length of a forward or reverse path restricts the entire email address to be no more than 254 characters long
    # https://en.wikipedia.org/wiki/Email_address#Syntax

    # For local-part:
    # Can contains:
    # uppercase and lowercase Latin letters A to Z and a to z;
    # digits 0 to 9;
    # special characters !#$%&'*+-/=?^_`{|}~;

    # Restrictions for local-part:
    # local part length <= 64 characters
    # '.'provided that it is not the first or last character unless quoted,
    # and provided also that it does not appear consecutively unless quoted
    # space and "(),:;<>@[\] are only allowed within a quoted string

    if chr(64) in user_email:  # chr(64) = @
        email_dissection = user_email.rpartition("@")  # partition @ from the back of the string
        localpart = email_dissection[0]
        domain = email_dissection[2]

        if len(user_email) > 254: #length too long
            return False

        else:
            if len(localpart) > 64: #local part too long
                return False

            else:
                list_of_exclusion = [chr(32), chr(34), chr(40), chr(41), \
                                     chr(44), chr(58), chr(59), chr(60), \
                                     chr(62), chr(64), chr(91), chr(92), \
                                     chr(93)]  # to account for space and "(),:;<>@[\]
                if localpart[0] == localpart[-1] == (chr(39) or chr(44)):  # chr(39)= ' #chr(44) = " #entire domain is quoted -> no error
                    pass
                else:
                    iteration = iteration_dot = 0
                    for character in localpart:
                        if character in list_of_exclusion: #local part contains invalid char
                           return False
                        elif character == chr(46):  # Purpose in this suite is to check if '.' appeared consecutively outside a quoted string
                            if iteration_dot == 0:
                                pass
                            elif iteration_dot == iteration - 1: #Local part contains consecutive '.'!
                               return False
                            iteration_dot = iteration  # update the location of the dot to its index
                        iteration += 1  # update the location of the character to the next index

            if len(domain) > 255: #domain too long
                return False
            else:
                if chr(46) not in domain: #no dot
                  return False
                else:
                    pass
    else:
        return False

    return True

def matricNumberCheck(num):
    sums = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L"]
    if len(num) != 9: return False
    elif num[0].upper() not in ['U', 'G','N']: return False
    elif num[8].upper() not in sums: return False
    else:
        for i in num[1:8]:
            if i not in string.digits: return False
        return True
