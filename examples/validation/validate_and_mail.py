#!/usr/bin/env python
"""
Validate a data file using cutplace and inform interested parties about the
outcome.

This is an example script, feel free to adjust for your own use starting with
the source code lines marked with "TODO". 

For more information on cutplace, visit <http://cutplace.sourceforge.net/>.
"""
import cutplace
import os
import os.path
import smtplib
from email.mime.text import MIMEText

if __name__ == '__main__':
    # TODO: Adjust sender and recipients to your own needs.
    sender = "quality.assurance@example.com"
    recipients = ["data.owner@example.com"]
    
    # TODO: Adjust the paths to your own needs. In practice you will use
    # absolute paths here, these are just relative paths to reuse existing
    # example data.
    icdPath = os.path.join(os.pardir, "icd_customers.ods")
    dataPath = os.path.join(os.pardir, "customers.csv")
    rejectedDataPath = os.path.join(os.pardir, "customers_rejected.txt")
    
    # Compute plain name of data file, for example "customer"
    dataName = os.path.splitext(os.path.split(dataPath)[1])[0]
    
    # Validate the data and set `subject` and `text` for the email.
    try:
        cutplace.main(["--split", icdPath, dataPath])
        # FIXME: Detect if data are broken because of failed checks at the end.
        dataAreOk = (os.path.getsize(rejectedDataPath) == 0)
        if dataAreOk:
            subject = "Validation ok: %s" % dataName
        else:
            subject = "Validation failed: %s" % dataName
            text = """Data: %s
ICD: %s""" % (icdPath, dataPath)
    except Exception, error:
        subject = "Validation error: %s" % dataName
        text = """Validation of %s failed

Reason: %s
Data: %s
ICD: %s""" % (dataName, error, icdPath, dataPath)
    
    # Build the email.
    COMMA_AND_SPACE = ", "
    message = MIMEText(text)
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = COMMA_AND_SPACE.join(recipients)
    
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    # TODO: Possibly adjust server and connection settings.
    session = smtplib.SMTP()
    session.sendmail(sender, recipients, message.as_string())
    session.quit()
