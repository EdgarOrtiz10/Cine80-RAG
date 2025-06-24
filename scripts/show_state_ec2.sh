PEM="ec2-edgar.pem"
USER="ubuntu"
HOST="18.230.58.17"

echo "Conectando a EC2 para verificar contenedores..."

ssh -i $PEM $USER@$HOST << EOF
echo "Estado actual de los contenedores:"
docker ps -a
EOF