import easySQL
import pathlib

@easySQL.Table
class Collections:
    def __init__(self) -> None:
        self.name = "Collections"
        self.columns = {
            'collection_id': easySQL.INTEGER,
            'version': easySQL.INTEGER,
            'uuid': easySQL.STRING,
            'name': easySQL.STRING,
            'settings': easySQL.JSON,
            'inheritance': easySQL.JSON,
            'character_links': easySQL.JSON
        }

@easySQL.Table
class CollectionMeta:
    def __init__(self) -> None:
        self.name = "MetaTable"
        self.columns = {
            'meta_id': easySQL.INTEGER,
            'collection_name': easySQL.STRING,
            'comments': easySQL.STRING,
            'version': easySQL.STRING
        }


@easySQL.Table
class Modifications:
    def __init__(self) -> None:
        self.name = "Modifications"
        self.columns = {
            'mod_id': easySQL.INTEGER,
            'fileversion': easySQL.INTEGER,
            'name': easySQL.STRING,
            'author': easySQL.STRING,
            'description': easySQL.STRING,
            'version': easySQL.INTEGER,
            'website': easySQL.STRING,
            'modtags': easySQL.JSON,
            'mod_path': easySQL.STRING,
            'total_files': easySQL.INTEGER
        }

collections = Collections()
modifications = Modifications()
metadata = CollectionMeta()

easySQL.intergrate(database_path=pathlib.Path('database.sqlite'))
easySQL.create_table(collections, drop=True)
easySQL.create_table(modifications, drop=True)
easySQL.create_table(metadata, drop=True)