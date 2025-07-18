import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user}としてログインしました！')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    # サムズアップ（👍）リアクションの場合
    if str(payload.emoji) == '👍':
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return
        
        await channel.send('投稿一覧の取得を開始します...')
        
        try:
            # メッセージ履歴を100件ずつ取得
            messages = []
            last_message = None
            batch_count = 0
            
            for batch in range(20):  # 最大20回（20 × 100 = 2000件）
                # 100件ずつ取得
                batch_messages = []
                async for message in channel.history(limit=100, before=last_message):
                    batch_messages.append({
                        'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'author': str(message.author),
                        'content': message.content,
                        'id': message.id
                    })
                    last_message = message
                
                # バッチが空の場合は終了
                if not batch_messages:
                    break
                
                messages.extend(batch_messages)
                batch_count += 1
                print(f'{batch_count * 100}件取得完了（実際: {len(messages)}件）')
                
                # 2秒間スリープ
                await asyncio.sleep(2)
            
            # テキストファイルを作成
            filename = f'channel_messages_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            filepath = f'/tmp/{filename}'
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f'チャンネル: {channel.name}\n')
                f.write(f'取得日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'取得件数: {len(messages)}件\n')
                f.write('=' * 50 + '\n\n')
                
                # メッセージを新しい順に並び替え（最新が上に）
                for msg in reversed(messages):
                    f.write(f'[{msg["timestamp"]}] {msg["author"]}\n')
                    f.write(f'{msg["content"]}\n')
                    f.write('-' * 30 + '\n')
            
            # ファイルをDiscordにアップロード
            with open(filepath, 'rb') as f:
                discord_file = discord.File(f, filename)
                await channel.send(
                    f'投稿一覧の取得が完了しました！\n取得件数: {len(messages)}件',
                    file=discord_file
                )
            
            # 一時ファイルを削除
            os.remove(filepath)
            
        except Exception as e:
            await channel.send(f'エラーが発生しました: {str(e)}')

if __name__ == '__main__':
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
    else:
        bot.run(TOKEN)