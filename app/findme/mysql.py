from django.db import connection, close_old_connections

__cursor = connection.cursor()


def mysql_select(query: str):
    __cursor.execute(query)
    columns = [col[0] for col in __cursor.description]
    res = [dict(zip(columns, row)) for row in __cursor.fetchall()]
    if not len(res):
        return None
    close_old_connections()
    return res


def mysql_update(query: str):
    __cursor.execute(query)
    close_old_connections()
    return


def mysql_insert(query: str):
    __cursor.execute(query)
    close_old_connections()
    return __cursor.lastrowid


def call_procedure(name: str, params: list):
    __cursor.callproc(procname=name, params=params)
    columns = [col[0] for col in __cursor.description]
    close_old_connections()
    return [
        dict(zip(columns, row)) for row in __cursor.fetchall()
    ]
