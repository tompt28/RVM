import smtplib
import ssl

# Email reporting
port = '465'  # for secure messages
smtp_server = 'smtp.gmail.com'
sender_email = "testpi.pneumatrol@gmail.com"
receiver_email = ""
password = "Pneumatroltest1!"


def erroremail(smtp, p, sender, key, receiver):
    """
    Function to send an email to the tester when a major error (loosing the output) occurs
    :param smtp:
    :param p:
    :param sender:
    :param key:
    :param receiver:
    :return: None
    """
    try:
        message = """\
                   Subject: RVM Testing Error

                    There has been a Fault on the RVM test causing no output to be found, Please review the testing. 

                    This message is sent automatically from the RVM Test unit, no reply is necessary."""

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp, p, context=context) as server:
            server.login(sender_email, key)
            server.sendmail(sender, receiver, message)
    except Exception as e:
        print(e)
