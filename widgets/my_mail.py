# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
def sendmail(toaddrs, msg, subject='chemdb synthesis'):
    import smtplib
    import string, sys
    fromaddr = 'adamed.chemdb@gmail.com'  
    toaddrs  = toaddrs
    msg = msg
    body = string.join((
    "From: %s" % fromaddr,
    "To: %s" % toaddrs,
    "Subject: %s" % subject,
    "",
    msg), "\r\n")
  
    # Credentials (if needed)  
    username = 'adamed.chemdb@gmail.com'  
    password = 'adamedic4u'  
      
    # The actual mail send  
    server = smtplib.SMTP('smtp.gmail.com:587')  
    server.starttls()  
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, body)  
    server.quit()  

if __name__ == "__main__":
    toaddrs = 'jasinski.adrian@gmail.com'
    msg = "test"
    sendmail(toaddrs, msg)
