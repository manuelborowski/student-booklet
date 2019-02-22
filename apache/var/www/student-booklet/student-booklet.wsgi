import sys, os
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/home/aboro/projects/student-booklet/venv/lib/python3.7/site-packages")
sys.path.insert(0,"/home/aboro/projects/student-booklet")

os.putenv('FLASK_CONFIG', 'production')

from app import create_app
config_name = os.getenv('FLASK_CONFIG')
config_name = 'production'
application = create_app(config_name)
#from test_smartschoolV2 import create_app
#application=create_app()
