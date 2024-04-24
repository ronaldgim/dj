#!/bin/bash

echo "Activando entorno virtual..."
source /var/www/html/dj/operaciones-env/bin/activate

echo "Realizando git pull..."
cd /var/www/html/dj
git pull origin master

echo "Instalando dependencias..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Listo."

