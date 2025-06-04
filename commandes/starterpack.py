from discord.ext import commands
import discord
import sqlite3
import datetime
import logging
import traceback

class StarterPack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="starterpack")
    async def starterpack_command(self, ctx):
        """Donne un pack de départ au joueur"""
        # Vérifier si la commande est utilisée en MP
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ Cette commande doit être utilisée en message privé avec le bot.")
            return

        try:
            logger = logging.getLogger('bot')
            player_info = self.bot.player_sync.db.get_player_info(str(ctx.author.id))
            if not player_info or not player_info[1]:
                await ctx.send("❌ Vous n'êtes pas encore enregistré. Utilisez la commande `!register` pour vous inscrire.")
                return
            discord_name, player_name, player_id, wallet, rp, date_end_rp, steam_id = player_info
            logger.info(f"Traitement starterpack pour {ctx.author.name} (Discord ID: {ctx.author.id})")
            logger.info(f"Informations joueur : Nom={player_name}, ID={player_id}, Steam ID={steam_id}")
            if not steam_id:
                await ctx.send("❌ Votre compte n'a pas de Steam ID associé. Veuillez contacter un administrateur.")
                logger.error(f"Pas de Steam ID pour le joueur {player_name} (Discord ID: {ctx.author.id})")
                return
            if self.bot.player_sync.db.has_received_starterpack(str(ctx.author.id)):
                await ctx.send("❌ Vous avez déjà reçu votre pack de départ. Cette commande ne peut être utilisée qu'une seule fois par joueur.")
                return
            online_players = self.bot.player_tracker.rcon_client.get_online_players()
            logger.info(f"Joueurs en ligne: {online_players}")
            is_valid_player_list = True
            for player in online_players:
                if "Couldn't find the command" in player or "Try \"help\"" in player:
                    is_valid_player_list = False
                    logger.error(f"Erreur dans la liste des joueurs: {player}")
                    break
            if not is_valid_player_list:
                try:
                    resp = self.bot.player_tracker.rcon_client.execute("ListPlayers")
                    logger.info(f"Réponse directe de ListPlayers: {resp}")
                    online_players = []
                    lines = resp.splitlines()
                    if lines and ("Idx" in lines[0] or "Char name" in lines[0]):
                        lines = lines[1:]
                    for line in lines:
                        if not line.strip():
                            continue
                        if "|" in line:
                            parts = line.split("|")
                            if len(parts) >= 2:
                                char_name = parts[1].strip()
                                if char_name and char_name != "Char name":
                                    online_players.append(char_name)
                                    logger.info(f"Joueur extrait manuellement: {char_name}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'extraction manuelle des joueurs: {e}")
            await ctx.send(f"ℹ️ Joueurs connectés: {', '.join(online_players)}")
            resp = self.bot.player_tracker.rcon_client.execute("ListPlayers")
            logger.info(f"Vérification de la présence du joueur avec Steam ID {steam_id}")
            is_player_online = False
            if resp and steam_id:
                lines = resp.splitlines()
                for line in lines:
                    if steam_id in line:
                        is_player_online = True
                        logger.info(f"Joueur avec Steam ID {steam_id} trouvé en ligne: {line}")
                        break
            if not is_player_online:
                await ctx.send(f"❌ Vous devez être connecté au serveur avec votre personnage '{player_name}' pour recevoir votre pack de départ.")
                return
            await ctx.send("⏳ Préparation de votre pack de départ, veuillez patienter...")
            logger.info(f"Tentative d'envoi du starter pack pour le joueur avec Steam ID {steam_id}")
            if await self.bot.item_manager.give_starter_pack_by_steam_id(steam_id):
                self.bot.player_sync.db.set_starterpack_received(str(ctx.author.id))
                await ctx.send(f"✅ Votre pack de départ a été ajouté à votre inventaire!\n"
                              f"Personnage : {player_name}\n"
                              f"Contenu : Piolet stellaire, couteau stellaire, grande hache stellaire, coffre en fer, cheval, selle légère et extrait d'aoles.")
                conn = sqlite3.connect('discord.db')
                c = conn.cursor()
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    c.execute("INSERT INTO item_transactions (discord_id, player_name, item_id, count, price, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (str(ctx.author.id), player_name, 0, 1, 0, "StarterPack Distribué", timestamp))
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                finally:
                    conn.close()
            else:
                await ctx.send("❌ Une erreur est survenue lors de l'ajout du pack de départ. Vérifiez que vous êtes bien connecté au serveur.")
        except Exception as e:
            logger = logging.getLogger('bot')
            logger.error(f"Erreur dans starterpack_command: {e}")
            logger.error(traceback.format_exc())
            await ctx.send("❌ Une erreur est survenue lors de l'ajout du pack de départ. Veuillez contacter un administrateur.")

async def setup(bot):
    await bot.add_cog(StarterPack(bot)) 