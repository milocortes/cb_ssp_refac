# Creación de base de datos

Para crear la base de datos, ejecuta : 

```shell
cat cb_database | sqlite3 cb_data.db
```

Para construir el orm model: 

```shell
sqlacodegen sqlite:///cb_data.db > cb_orm_model.py
```