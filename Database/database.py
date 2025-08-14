import psycopg2
from sshtunnel import SSHTunnelForwarder
import time

with SSHTunnelForwarder(
         ('192.168.190.65', 22),
         ssh_password="AdmRT2023!",
         ssh_username="admrt",
         remote_bind_address=('192.168.190.65', 5432)) as server:

    conn = psycopg2.connect(
        host="192.168.190.65",
        database="ProjectDocumentationSynthesis",
        user="TestUser",
        password="test1"
    )

    curs = conn.cursor()
    sql = "select 1"
    curs.execute(sql)
    rows = curs.fetchall()
    print(rows)