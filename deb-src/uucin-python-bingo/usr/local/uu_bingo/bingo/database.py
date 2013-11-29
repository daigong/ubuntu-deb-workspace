import xapian
import psycopg2
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
_settings = None


def configure(settings):
    global _settings
    _settings = settings


def get_xapian_conn(readonly=True):
    if not readonly:
        return xapian.WritableDatabase(
            _settings['xapian.database.path'],
            xapian.DB_CREATE_OR_OPEN
        )
    elif _settings:
        _readonly_xapian_conn = xapian.Database(
            _settings['xapian.database.path']
        )
        return _readonly_xapian_conn
    else:
        raise TypeError("not call configure method")


def get_postgres_conn():
    if _settings:
        return psycopg2.connect(
            database=_settings['postgresql.database'],
            user=_settings['postgresql.username'],
            password=_settings['postgresql.password'],
            host=_settings['postgresql.host'],
            port=_settings['postgresql.port'],
        )
    else:
        raise TypeError("not call configure method")
