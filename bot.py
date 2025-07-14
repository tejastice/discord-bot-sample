import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user}としてログインしました！')
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)}個のスラッシュコマンドを同期しました')
    except Exception as e:
        print(f'スラッシュコマンドの同期に失敗しました: {e}')

@bot.tree.command(name="help", description="このボットの使い方を表示します")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Discord Bot ヘルプ",
        description="このボットの使い方をご説明します！",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📝 基本機能",
        value="• メッセージを送ると「こんにちは。はろー！よろしくね」と返答します\n• スラッシュコマンドに対応しています",
        inline=False
    )
    
    embed.add_field(
        name="⚡ スラッシュコマンド",
        value="• `/help` - このヘルプメッセージを表示",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ 注意事項",
        value="• ボット自身のメッセージには反応しません\n• すべてのメッセージに自動返答します",
        inline=False
    )
    
    embed.set_footer(text="何かご質問があればお気軽にどうぞ！")
    
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await message.channel.send('こんにちは。はろー！よろしくね')
    
    await bot.process_commands(message)

if __name__ == '__main__':
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
    else:
        bot.run(TOKEN)