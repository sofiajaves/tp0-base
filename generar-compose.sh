#!/bin/bash

#Generar un docker compose con una cantidad de clientes por coomando:

# como se corre con ./generar-compose.sh docker-compose-dev.yaml 5
# significa que corro el script de bash, luego el compose (nombre del archivo) y la cantidad de clientes que quiero

# VERIFICO QUE SE HAYAN PASADO 2 ARGUMENTOS
if [ "$#" -ne 2 ]; then
    echo "Error: Must enter 2 arguments"
    exit 1
fi

FILE_NAME=$1
CLIENTS=$2

# Verifico que el numero sea correcto (solo enteros)
if ! [[ "$CLIENTS" =~ ^[0-9]+$ ]]; then
    echo "Error: Client number must be an integer"
    exit 1
fi

# Invoco un subscript de python para modificar el archivo de docker-compose.yaml
python3 mi-generador.py "$FILE_NAME" "$CLIENTS"

echo "Docker compose updated with $CLIENTS clients"