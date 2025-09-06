from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from web_app.app.config import Config
from fastapi.templating import Jinja2Templates


router = APIRouter()


templates = Jinja2Templates(directory=Config.TEMPLATES_PATH)