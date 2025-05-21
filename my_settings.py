import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

DATABASES = {
    'default' : {
        'ENGINE': 'django.db.backends.mysql',   
        'NAME': os.getenv('DB_NAME', 'HOUSCAN'),               
        'USER': os.getenv('DB_USER', 'django_user'),                   
        'PASSWORD': os.getenv('DB_PASSWORD',''),    
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),        
        'PORT': os.getenv('DB_PORT', '3306'),    
        'OPTIONS':  {'charset': 'utf8mb4'},
    }
}