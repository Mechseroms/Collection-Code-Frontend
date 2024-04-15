from typing import Any
import sqlite3, pathlib
from collections import namedtuple

STRING = 'string'
INTEGER = 'integer'
UNIQUE = 'UNIQUE'
JSON = 'json' # TODO: create a function for converting lists and dict into json string and back
database = None

def VALDATED_STRING(pointer, direction=0):
    """ 
        direction(0) = into database
        direction(1) = out of database
    """
    if direction == 0:
        return pointer.replace("'", "%^&*").strip()
    elif direction == 1:
        return pointer.replace("%^&*", "'").strip()


def intergrate(database_path: pathlib.Path = None) -> sqlite3.Connection:

    if not database_path:
        database_path = pathlib.Path("test.sqlite")

    global database 
    database = sqlite3.connect(database=database_path.absolute())
    return database


def Table(cls):
    """ easySQL decorator for table classes for easy instantiation of many of the SQL_execute strings.

    This class will always need these variables defined within its __init__ method;

    self.name = "foo";  This will be the name of the table in the integrated database
    self.columns = {foo: dah, ...}; dictionary of foo being the column name, and dah being the columns type in the database
        types for a column are:
            - STRING
            - INTEGER
            - UNIQuE
            - JSON

    Returns:
        Table: returns a Table class wrapped around the original class.
    """
    class Table(cls):
        def __init__(self, *args, **kwargs) -> None:
            super(Table, self).__init__(*args, **kwargs)
            self.data_object = namedtuple(f"{self.name}_row", list(self.columns.keys()))
            self.columns_validation = len(self.columns)
        
        def __repr__(self):
            return f"{self.__class__.__name__} ('{self.name}')"
        
        @property
        def create_table(self):
            def manufacture_create_SQL_string() -> str:
                """ Takes the super()'s columns dictionary and bulds parts of the SQL_execute string.

                Returns:
                    str: middle of create table SQL_execute string.
                """
                # TODO: very crude way of doing it, research a better way.
                middle_string = 'id integer PRIMARY KEY, '
                current_count = 0
                for column_name, column_type in self.columns.items():
                    if column_type == 'json':
                        column_type == 'string'
                    if current_count == len(self.columns.items())-1:
                        middle_string += f"{column_name} {column_type}"
                    else:
                        middle_string += f"{column_name} {column_type}, "
                    current_count += 1
                return middle_string
            return f"CREATE TABLE {self.name} ({manufacture_create_SQL_string()});"    
        
        @property
        def drop_table(self):
            return f"DROP TABLE {self.name};"
        
        def select_row(self, column: str = None, match = None):
            if column:
                column_type = self.columns[column]
                if column_type == "string": match = VALDATED_STRING(match, direction=0)
                return f"SELECT * FROM {self.name} WHERE {column}= '{match}'"
            else:
                return f"SELECT * FROM {self.name}"
        
        def insert_row(self, data) -> namedtuple:
            __conversion__ = []
            for id, pointer in enumerate(data):
                column_type = list(self.columns.values())[id]
                if isinstance(pointer, str) and column_type != "json":
                    pointer = VALDATED_STRING(pointer, direction=0)
                __conversion__.append(pointer)
            __conversion__ = tuple(__conversion__)

            def manufacture_insert_SQL_String():
                middle_string = '('
                gavel_string = '('
                current_count = 0
                for column_name in self.columns.keys():
                    if current_count == len(self.columns.items())-1:
                        middle_string += f"{column_name})"
                        gavel_string += f"?)"
                    else:
                        middle_string += f"{column_name}, "
                        gavel_string += f"?, "
                    current_count += 1
                return f"{middle_string} VALUES {gavel_string}"
            
            query = namedtuple('Query', ['query', 'data'])
            if len(__conversion__) == self.columns_validation:
                return query(query=f"INSERT INTO {self.name}{manufacture_insert_SQL_String()}", data=__conversion__)
            else:
                return query(query=False, data= f"passed data to {self.name} is not the right length of entries")
        
        def update_row_by_id(self, data: dict, id: str):
            """ Update a row at {id} with {data}.

            Args:
                data (dict): key = column, value = data to update to
                id (str): row_id in Table
            """
            def manufactur_update_SQL_string(data: dict) -> str:
                """ takes data and builds a SQL_execute string segment

                Args:
                    data (dict): Key = column, value = data to update to

                Returns:
                    _type_: middle segment of SQL_execute string
                """
                # TODO: this is a very crude implementtion
                middle_string = ''
                current_count = 0
                for key, value in data.items():
                    if current_count == len(data.items())-1:
                        middle_string += f" {key} = '{value}'"
                    else:
                        middle_string += f" {key} = '{value}', "
                    current_count += 1
                return middle_string
            return f"UPDATE {self.name} SET{manufactur_update_SQL_string(data)} WHERE id = {id}"

        def convert_data(self, rows: list or tuple):
            """ Takes rows returned by the tables SQL_select string and returns them as namedtuples.

            Args:
                rows (listortuple): 

            Returns:
                (listortuple): returns a list of namedtuple.
            """

            self.keys = list(self.columns.keys())
            
            if isinstance(rows, list):
                pointer_list =[]
                for row in rows:
                    __conversion__ = []
                    for id, pointer in enumerate(row):
                        column_type = list(self.columns.values())[id-1]
                        if isinstance(pointer, str) and column_type != "json":
                            pointer = VALDATED_STRING(pointer, direction=1)
                        __conversion__.append(pointer)
                    __conversion__ = tuple(__conversion__)
                    pointer_list.append(__conversion__)
                return [self.data_object(**{key: data[i+1] for i, key in enumerate(self.keys)}) for data in pointer_list]
            
            if isinstance(rows, tuple):
                __conversion__ = []
                for id, pointer in enumerate(rows):
                    column_type = list(self.columns.values())[id-1]
                    if isinstance(pointer, str) and column_type != "json":
                        pointer = VALDATED_STRING(pointer, direction=1)
                    __conversion__.append(pointer)
                __conversion__ = tuple(__conversion__)
                return [self.data_object(**{key: __conversion__[i+1] for i, key in enumerate(self.keys)})][0]
        
        
    return Table


def basic_query(query: str):
    """ Used as single query functions, ex. creating tables, dropping tables, updating rows

    Args:
        query (str): SQL_execute string
    """
    with database:
        cursor = database.cursor()            
        cursor.execute(query)
        
def create_table(table: Table, drop=False):
    
    if drop:
        drop_table(table=table)
        
    try:
        with database:
            cursor = database.cursor()            
            cursor.execute(table.create_table)
    except sqlite3.OperationalError:
        pass
    
def drop_table(table: Table):
    try:
        with database:
            cursor = database.cursor()            
            cursor.execute(table.drop_table)
    except sqlite3.OperationalError:
        pass
    
    
def update_table_row_by_id(table: Table, row):
    query = table.update_row_by_id(data=row[1], id=row[0])
    with database:
        cursor = database.cursor()            
        cursor.execute(query)


def insert_into_table(table, data):
    """ Passing a query and its data as a namedtuple will insert the query into the database.

    Args:
        query (namedtuple): (query.query = SQL_execute string, query.data = tuple of column's data)
    """
    query = table.insert_row(data)
    assert query.query, query.data
    with database:
        cursor = database.cursor()
        cursor.execute(query.query, query.data)
    
def fetchone_from_table(table: Table, filter: tuple([str, Any]) = None, convert_data=True) -> tuple:
    if filter:
        query = table.select_row(column=filter[0], match=filter[1])
    else:
        query = table.select_row()
    
    with database:
        cursor = database.cursor()
        cursor.execute(query)

        if not convert_data:
            return cursor.fetchone()
        
        return table.convert_data(cursor.fetchone())
        
    
def fetchall_from_table(table, filter: tuple([str, Any]) = None, convert_data=True) -> list:
    """ Fetches all rows from the database using passed query

    Args:
        query (str): SQL_execute string

    Returns:
        list: list of rows as tuples
    """

    if filter:
        query = table.select_row(column=filter[0], match=filter[1])
    else:
        query = table.select_row()

    with database:
        cursor = database.cursor()
        cursor.execute(query)
        batch = cursor.fetchall()
        
        if len(batch) == 1:
            batch = batch[0]

        if not convert_data:
            return batch
        
        return table.convert_data(batch)