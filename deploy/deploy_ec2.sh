#!/bin/bash

PEM="ec2-edgar.pem"
USER="ubuntu"
HOST="18.230.58.17"
REMOTE_DIR="/home/ubuntu/app"
CONTAINER="rag-backend"

echo "Iniciando despliegue en EC2..."

# 1. Subida de archivos
echo "Subiendo archivos al servidor EC2..."
scp -i "$PEM" -r ../app ../api.py ../requirements.txt ../.env "$USER@$HOST:$REMOTE_DIR"
if [ $? -ne 0 ]; then
  echo "Error: Falló la subida de archivos. Revisa la ruta del archivo PEM o la conexión SSH."
  exit 1
fi

# 2. Reiniciar contenedor
echo "Reiniciando contenedor Docker..."
ssh -i "$PEM" "$USER@$HOST" << EOF
cd $REMOTE_DIR || exit 1
docker restart $CONTAINER || exit 1
docker ps -a | grep $CONTAINER
EOF

if [ $? -ne 0 ]; then
  echo "Error: Falló la conexión SSH o el reinicio del contenedor."
  exit 1
fi

echo "Despliegue completado correctamente en EC2."
