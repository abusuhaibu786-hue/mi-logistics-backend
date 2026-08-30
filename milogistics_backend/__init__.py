# Makes PyMySQL act as MySQLdb so Django's `django.db.backends.mysql`
# engine works without needing the mysqlclient C extension (which requires
# a C compiler + MySQL dev headers to build on Windows).
import pymysql

pymysql.install_as_MySQLdb()
