from settings_local import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


class Config(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    POSTGRES = {
        'user': DB_USER,
        'pw': DB_PASSWORD,
        'db': DB_NAME,
        'host': DB_HOST,
        'port': DB_PORT,
    }

    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
