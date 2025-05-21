import os

DATABASES = {
    'default' : {
        'ENGINE': 'django.db.backends.mysql',   
        'NAME': os.getenv('DB_NAME', 'HOUSCAN'),               
        'USER': os.getenv('DB_USER', 'root'),                   
        'PASSWORD': os.getenv('DB_PASSWORD',''),    
        'HOST': os.getenv('DB_HOST', 'localhost'),        
        'PORT': os.getenv('DB_PORT', '3306'),    
        'OPTIONS':  {'charset': 'utf8mb4'},
    }
}