from django.db import connection

__cursor = connection.cursor()


def query_mysql(query: str):
    __cursor.execute(query)
    columns = [col[0] for col in __cursor.description]
    return [
        dict(zip(columns, row)) for row in __cursor.fetchall()
    ]
