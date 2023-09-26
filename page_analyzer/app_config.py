import os
from dotenv import load_dotenv
from polog import config, file_writer

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')


conf = config.add_handlers(file_writer('app_logs'))
