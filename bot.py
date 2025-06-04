import os
import discord
import ssl
import logging
import sqlite3
import datetime
import traceback
from discord.ext import commands
from dotenv import load_dotenv
from features.player_tracker import PlayerTracker
from utils.rcon_client import RCONClient
from utils.ftp_handler import FTPHandler
from features.build_limit import BuildLimitTracker
from features.classement_player import KillTracker
from features.player_sync import PlayerSync
from features.vote_tracker import VoteTracker
from features.item_manager import ItemManager
from database.init_database import init_database
import glob

# Configuration SSL pour Python 3.13
ssl._create_default_https_context = ssl._create_unverified_context

# Initialiser la base de données
init_database()

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True  # Permet de recevoir les messages privés
intents.members = True      # Permet d'accéder aux informations des membres
bot = commands.Bot(command_prefix='!', intents=intents)

# Récupération des variables d'environnement avec valeurs par défaut
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("Le token Discord n'est pas défini dans le fichier .env")

RENAME_CHANNEL_ID = int(os.getenv('RENAME_CHANNEL_ID', '1375223092892401737'))
BUILD_CHANNEL_ID = int(os.getenv('BUILD_CHANNEL_ID', '1375234869071708260'))
KILLS_CHANNEL_ID = int(os.getenv('KILLS_CHANNEL_ID', '1375234869071708260'))
TOP_SERVER_CHANNEL_ID = int(os.getenv('TOP_SERVER_CHANNEL_ID', '1368550677030109225'))
SERVER_PRIVE_CHANNEL_ID = int(os.getenv('SERVER_PRIVE_CHANNEL_ID', '1369099859574915192'))
LOG_FILE_PATH = os.getenv('FTP_LOG_PATH', 'Saved/Logs/ConanSandbox.log')

print(f"Configuration RCON:")
print(f"- Host: {os.getenv('GAME_SERVER_HOST')}")
print(f"- Port: {os.getenv('RCON_PORT')}")
print(f"- Password: {'*' * len(os.getenv('RCON_PASSWORD', '')) if os.getenv('RCON_PASSWORD') else 'Non défini'}")

# Initialisation des clients et trackers
rcon_client = RCONClient()
ftp_handler = FTPHandler()

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté à Discord!')
    try:
        # Initialisation des trackers
        bot.player_tracker = PlayerTracker(bot=bot, channel_id=RENAME_CHANNEL_ID, rcon_client=rcon_client)
        bot.build_tracker = BuildLimitTracker(bot=bot, channel_id=BUILD_CHANNEL_ID, ftp_handler=ftp_handler)
        bot.kill_tracker = KillTracker(bot=bot, channel_id=KILLS_CHANNEL_ID)
        bot.player_sync = PlayerSync(bot, LOG_FILE_PATH, ftp_handler=ftp_handler)
        bot.vote_tracker = VoteTracker(bot, TOP_SERVER_CHANNEL_ID, SERVER_PRIVE_CHANNEL_ID, ftp_handler=ftp_handler)
        bot.item_manager = ItemManager(bot, ftp_handler=ftp_handler)

        # Démarrage des trackers
        await bot.player_tracker.start()
        await bot.build_tracker.start()
        await bot.kill_tracker.start()
        await bot.player_sync.start()
        await bot.vote_tracker.start()
        
        print("Tous les trackers sont démarrés avec succès!")
        
    except Exception as e:
        print(f"Erreur lors du démarrage des trackers: {e}")

def load_all_cogs(bot):
    commandes_path = os.path.join(os.path.dirname(__file__), 'commandes')
    for file in glob.glob(os.path.join(commandes_path, '*.py')):
        if not file.endswith('__init__.py'):
            module = f"commandes.{os.path.splitext(os.path.basename(file))[0]}"
            try:
                bot.load_extension(module)
            except Exception as e:
                print(f"Erreur lors du chargement du module {module}: {e}")

load_all_cogs(bot)

# Lancer le bot
bot.run(DISCORD_TOKEN) 