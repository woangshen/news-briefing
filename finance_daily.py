#!/usr/bin/env python3
import os, smtplib, ssl
from email.mime.text import MIMEText
from email.header import Header
u = os.environ.get("SMTP_USER", "")
p = os.environ.get("SMTP_PASS", "")
t = os.environ.get("RECEIVER", u)
m = MIMEText("<h1>test</h1><p>if you got this, SMTP works</p>", "html", "utf-8")
m["Subject"] = Header("SMTP test from codex", "utf-8")
m["From"] = "test <"+u+">"
m["To"] = t
c = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.163.com", 465, context=c, timeout=30) as s:
  s.login(u, p)
  s.sendmail(u, [t], m.as_string())
print("done")
