# -*- coding: utf-8 -*-
"""Sample controller with all its actions protected."""
def sendmail(toaddrs, msg, subject='chemdb synthesis'):
    import smtplib
    import string
    fromaddr = 'molgears@mydomain.com'  
    toaddrs  = toaddrs
    msg = msg
    body = string.join((
    "From: %s" % fromaddr,
    "To: %s" % toaddrs,
    "Subject: %s" % subject,
    "",
    msg), "\r\n")
  
    # Credentials (if needed)  
#    username = ''  
#    password = ''
    try:
        # The actual mail send  
        server = smtplib.SMTP('localhost')  
    #    server.starttls()  
    #    server.login(username,password)
        server.sendmail(fromaddr, toaddrs, body)  
        server.quit()
    except Exception:
        print "Error: unable to send email"
