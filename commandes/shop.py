import os
import discord
from discord.ext import commands

SHOP_CHANNEL_ID = int(os.getenv('SHOP_CHANNEL_ID', 1379725647579975730))
COMMANDE_CHANNEL_ID = int(os.getenv('COMMANDE_CHANNEL_ID', 1375046216097988629))

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shop_channel_id = SHOP_CHANNEL_ID
        self.command_channel_id = COMMANDE_CHANNEL_ID
        print(f"✅ Cog Shop initialisé avec les IDs: Shop={self.shop_channel_id}, Commande={self.command_channel_id}")

    @commands.command()
    async def shop(self, ctx):
        """
        Quand on tape !shop DANS LE CHANNEL DÉFINI PAR COMMANDE_CHANNEL_ID,
        on envoie un message dans le channel défini par SHOP_CHANNEL_ID.
        """
        print(f"Commande shop appelée dans le channel {ctx.channel.id}")
        print(f"Channel attendu: {self.command_channel_id}")
        
        # Vérifier que la commande est utilisée dans le bon channel
        if ctx.channel.id != self.command_channel_id:
            print(f"❌ Mauvais channel. Channel actuel: {ctx.channel.id}, Channel attendu: {self.command_channel_id}")
            await ctx.send("❌ Cette commande ne peut être utilisée que dans le channel de commandes.")
            return

        shop_channel = self.bot.get_channel(self.shop_channel_id)
        if shop_channel is None:
            print(f"❌ Channel shop non trouvé (ID: {self.shop_channel_id})")
            await ctx.send("❌ Le channel de shop n'a pas été trouvé (vérifiez SHOP_CHANNEL_ID).")
            return

        print(f"✅ Envoi du message dans le channel shop (ID: {self.shop_channel_id})")
        # Envoyer le message dans le channel shop
        await shop_channel.send("Commande réussie pour voir")
        await ctx.send("✅ Message posté dans le channel shop !")
        #construit le shop en bouclan sur la table items et en envoyant un message dans le channel shop avec le nom de l'item, le prix et la quantité

async def setup(bot):
    print("Chargement du Cog Shop...")
    await bot.add_cog(Shop(bot))
    print("✅ Cog Shop chargé avec succès")