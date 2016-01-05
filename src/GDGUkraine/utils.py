import base64
import json
import logging
import os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import cherrypy as cp

from blueberrypy.template_engine import get_template

import html2text

from Crypto.Cipher import AES


logger = logging.getLogger(__name__)

# TODO: make this stuff normal
card_secret_key = os.getenv('CARD_SECRET_KEY',
                            'sHsagghsSBackFbscoEhTdBtpQtsszds')
card_cipher = AES.new(card_secret_key)


def is_admin():
    return isinstance(cp.session.get('admin_user'), dict) and \
        isinstance(cp.session.get('google_oauth'), dict) and \
        isinstance(cp.session.get('google_user'), dict)


def gmail_send(oauth2session, message, sbj, to_email,
               from_email='GDG Team Robot <kyiv@gdg.org.ua>'):

    message['to'] = to_email
    message['from'] = from_email
    message['subject'] = sbj

    st = oauth2session.post(
        'https://www.googleapis.com/gmail/v1/users/{userId}/messages/send'
        .format(userId='me'),
        data=json.dumps({'raw': base64.urlsafe_b64encode(message.as_string()
                                                         .encode('utf8'))
                        .decode('utf8')}),
        headers={"content-type": "application/json"})

    logger.debug(st.json())
    return st.json()


def gmail_send_html(oauth2session, template, payload, **kwargs):

    assert isinstance(payload, dict), 'gmail_send_html only accepts dict'

    msg = MIMEMultipart('alternative')

    html_payload = get_template(template).render(**payload)

    plain_text_payload = html2text.html2text(html_payload)

    msg.attach(MIMEText(plain_text_payload, 'plain'))
    msg.attach(MIMEText(html_payload, 'html'))

    return gmail_send(oauth2session, message=msg, **kwargs)


def gmail_send_text(oauth2session, payload, **kwargs):

    msg = MIMEText(payload)

    return gmail_send(oauth2session, message=msg, **kwargs)


def aes_encrypt(text):
    return card_cipher.encrypt(text).encode('utf8')


def aes_decrypt(text):
    return card_cipher.decrypt(text).encode('utf8')