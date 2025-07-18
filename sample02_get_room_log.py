import discord
from discord.ext import commands
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_CHANNEL_ID = 1394203406574424104  # ログを記録する対象チャンネル

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ログファイルのパス
LOG_FILE_PATH = 'room_log.txt'

def write_log(message_data):
    """ログファイルにメッセージを記録"""
    try:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(f'[{message_data["timestamp"]}] {message_data["author"]}: {message_data["content"]}\n')
    except Exception as e:
        print(f'ログ書き込みエラー: {e}')

@bot.event
async def on_ready():
    print(f'{bot.user}としてログインしました！')
    print(f'チャンネルID {TARGET_CHANNEL_ID} のログを記録開始します')
    
    # ログファイルの初期化（起動時のみ）
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(f'=== ルームログ開始: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ===\n')

@bot.event
async def on_message(message):
    # 対象チャンネルのメッセージのみ記録（Bot自身のメッセージも含む）
    if message.channel.id == TARGET_CHANNEL_ID:
        message_data = {
            'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'author': str(message.author),
            'content': message.content,
            'id': message.id
        }
        
        # ログファイルに記録
        write_log(message_data)
        print(f'ログ記録: [{message_data["timestamp"]}] {message_data["author"]}: {message_data["content"][:50]}...')
    
    # コマンド処理
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    # 対象チャンネルでのグッドマークリアクションのみ処理
    if payload.channel_id == TARGET_CHANNEL_ID and str(payload.emoji) == '👍':
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return
        
        try:
            # ログファイルが存在するかチェック
            if not os.path.exists(LOG_FILE_PATH):
                await channel.send('ログファイルが見つかりません。まだメッセージが記録されていないようです。')
                return
            
            # ログファイルのサイズをチェック
            file_size = os.path.getsize(LOG_FILE_PATH)
            if file_size == 0:
                await channel.send('ログファイルが空です。まだメッセージが記録されていないようです。')
                return
            
            # ファイルサイズが25MB以下かチェック（Discordの制限）
            if file_size > 25 * 1024 * 1024:  # 25MB
                await channel.send('ログファイルが大きすぎます（25MB以上）。ファイルを分割する必要があります。')
                return
            
            # ログファイルをDiscordにアップロード
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'room_log_{current_time}.txt'
            
            with open(LOG_FILE_PATH, 'rb') as f:
                discord_file = discord.File(f, filename)
                
                # ファイル情報を取得
                with open(LOG_FILE_PATH, 'r', encoding='utf-8') as log_f:
                    lines = log_f.readlines()
                    line_count = len(lines)
                
                await channel.send(
                    f'ルームログをお送りします！\n'
                    f'記録行数: {line_count}行\n'
                    f'ファイルサイズ: {file_size:,}バイト',
                    file=discord_file
                )
                print(f'ログファイルをアップロードしました: {filename}')
            
        except Exception as e:
            await channel.send(f'ログファイルの送信中にエラーが発生しました: {str(e)}')
            print(f'ログファイル送信エラー: {e}')

@bot.command(name='log_status')
async def log_status(ctx):
    """ログファイルの状態を確認するコマンド"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        return
    
    if os.path.exists(LOG_FILE_PATH):
        file_size = os.path.getsize(LOG_FILE_PATH)
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            line_count = len(lines)
        
        await ctx.send(
            f'📊 ログファイル状態\n'
            f'ファイルサイズ: {file_size:,}バイト\n'
            f'記録行数: {line_count}行\n'
            f'最終更新: {datetime.fromtimestamp(os.path.getmtime(LOG_FILE_PATH)).strftime("%Y-%m-%d %H:%M:%S")}'
        )
    else:
        await ctx.send('ログファイルはまだ作成されていません。')

if __name__ == '__main__':
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
    else:
        bot.run(TOKEN)