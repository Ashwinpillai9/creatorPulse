from dotenv import load_dotenv

load_dotenv()  # Ensure environment variables from .env are available before other imports

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import feedback, newsletter, sources

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.getenv(
    'LOG_FORMAT', '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
)

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

app = FastAPI(title='CreatorPulse API', version='0.1.0')

allowed_origins_env = os.getenv('ALLOWED_ORIGINS', '')
allowed_origins = [
    origin.strip() for origin in allowed_origins_env.split(',') if origin.strip()
]
if not allowed_origins:
    allowed_origins = ['*']

allow_credentials = os.getenv('ALLOW_CREDENTIALS', 'true').lower() == 'true'
if allowed_origins == ['*']:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=['*'],
    allow_headers=['*'],
)

logger.info('CreatorPulse API initialised with log level %s', LOG_LEVEL)

app.include_router(sources.router, prefix='/sources', tags=['Sources'])
app.include_router(newsletter.router, prefix='/newsletter', tags=['Newsletter'])
app.include_router(feedback.router, prefix='/feedback', tags=['Feedback'])


@app.get('/health')
def health():
    logger.debug('Health check requested')
    return {'status': 'ok'}

