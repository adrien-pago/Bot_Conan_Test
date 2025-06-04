import os
import discord
from discord.ext import commands
SHOP_CHANNEL_ID = int(os.getenv('SHOP_CHANNEL_ID', 1379725647579975730))
COMMANDE_CHANNEL_ID = int(os.getenv('COMMANDE_CHANNEL_ID', 1375046216097988629))
class Shop(commands.Cog):
    def init(self, bot):
        self.bot = bot
        self.shop_channel_id = SHOP_CHANNEL_ID
        self.command_channel_id = COMMANDE_CHANNEL_ID

    @commands.command(name='shop')
    async def shop_command(self, ctx):
        """
        Quand on tape !shop DANS LE CHANNEL DÉFINI PAR COMMANDE_CHANNEL_ID,
        on envoie un message dans le channel défini par SHOP_CHANNEL_ID.
        """
        # Vérifier que la commande est utilisée dans le bon channel
        if ctx.channel.id != self.command_channel_id:
            return  # On ignore silencieusement ou on pourrait renvoyer un message d'erreur

        shop_channel = self.bot.get_channel(self.shop_channel_id)
        if shop_channel is None:
            await ctx.send("❌ Le channel de shop n'a pas été trouvé (vérifiez SHOP_CHANNEL_ID).")
            return

        # Envoyer le message dans le channel shop
        await shop_channel.send("Commande réussie pour voir")
        # (Optionnel) Confirmer à l'utilisateur que la commande a bien été exécutée
        # await ctx.send("✅ Message posté dans le channel shop !")

def setup(bot):
    bot.add_cog(Shop(bot))