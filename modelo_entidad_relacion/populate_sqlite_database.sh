#!/bin/bash

if [ -f cb_data.db ]; then
    echo "Eliminamos cb_data.db"
    rm cb_data.db
fi

echo "Creamos cb_data.db"

cat cb_database | sqlite3 cb_data.db

for filename_path in csv2sqlite/*.csv; do
    filename=${filename_path##*/}
    echo "Poblando la tabla ${filename%.*} a partir del csv ${filename_path}"
    sqlite3 -separator ',' cb_data.db ".import ${filename_path} ${filename%.*}"
done