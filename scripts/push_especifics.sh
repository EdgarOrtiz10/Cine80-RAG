PEM="ec2-edgar.pem"
USER="ubuntu"
HOST="18.230.58.17"
LOCAL_FILE="api.py"
REMOTE_PATH="/home/ubuntu/app/"
CONTAINER="rag-backend"

echo "Subiendo $LOCAL_FILE al EC2..."
scp -i $PEM $LOCAL_FILE $USER@$HOST:$REMOTE_PATH

if [ $? -ne 0 ]; then
  echo "Error al subir el archivo."
  exit 1
fi

echo "Reiniciando contenedor Docker '$CONTAINER' en el servidor..."
ssh -i $PEM $USER@$HOST << EOF
cd /home/ubuntu/app
docker restart $CONTAINER
EOF

echo "Código actualizado y contenedor reiniciado correctamente."
