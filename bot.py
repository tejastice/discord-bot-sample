import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from datetime import time

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

@tasks.loop(time=time(hour=6, minute=0))  # 毎日朝6時に実行
async def periodic_good_morning():
    channel = bot.get_channel(1394203406574424104)  # 指定されたチャンネル
    if channel:
        await channel.send('おはようございます')

@bot.event
async def on_ready():
    print(f'{bot.user}としてログインしました！')
    try:
        # 指定されたギルドの既存コマンドをクリア
        guild = discord.Object(id=1394139562028306644)
        bot.tree.clear_commands(guild=guild)
        
        # グローバルコマンドを同期
        synced_global = await bot.tree.sync()
        print(f'{len(synced_global)}個のグローバルスラッシュコマンドを同期しました')
        
        # ギルド専用コマンドを同期
        synced_guild = await bot.tree.sync(guild=guild)
        print(f'{len(synced_guild)}個のギルド専用スラッシュコマンドを同期しました')
        
        # 定期投稿を開始
        periodic_good_morning.start()
        print('定期投稿を開始しました（毎朝6時に「おはようございます」）')
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
        value="• `/help` - このヘルプメッセージを表示\n• `/information` - 情報を提供します",
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
    
    await message.reply(message.content)
    
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    # サムズアップ（👍）リアクションの場合
    if str(payload.emoji) == '👍':
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        message_content = message.content[:50]  # メッセージの最初の50文字
        if len(message.content) > 50:
            message_content += "..."
        
        await channel.send(
            f'グッドマークが押されたよ！「{message_content}」のメッセージにグッドマークが押されたよ'
        )

if __name__ == '__main__':
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
    else:
        bot.run(TOKEN)