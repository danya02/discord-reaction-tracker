import discord
import os
from database import *

import logging
logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')

bot = discord.Client()

bot.run(TOKEN)
