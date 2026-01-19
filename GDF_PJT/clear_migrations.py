#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GDF_PJT.settings')

# Configure Django settings
import sys
sys.path.insert(0, r'c:\Users\pedro.silva\Documents\Visual Studio Code\GDF_V2\GDF_PJT')

django.setup()

from django.db import connection
with connection.cursor() as c:
    c.execute('DELETE FROM django_migrations WHERE app = %s', ['app'])
    
print('✓ Migration records deleted')
