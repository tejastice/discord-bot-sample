import discord
from discord.ext import commands
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True  # メンバー情報を取得するために必要

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user}としてログインしました！')
    print('グッドマークのリアクションでサーバーのメンバー一覧を取得します')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    # サムズアップ（👍）リアクションの場合
    if str(payload.emoji) == '👍':
        channel = bot.get_channel(payload.channel_id)
        guild = channel.guild if channel else None
        
        if not channel or not guild:
            return
        
        await channel.send('サーバーのメンバー一覧を取得中です...')
        
        try:
            # メンバー一覧を取得
            members = []
            member_count = 0
            
            # ギルドのメンバーを取得
            async for member in guild.fetch_members(limit=None):
                member_info = {
                    'id': member.id,
                    'name': member.name,
                    'display_name': member.display_name,
                    'discriminator': member.discriminator,
                    'joined_at': member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else 'N/A',
                    'created_at': member.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_bot': member.bot,
                    'status': str(member.status),
                    'roles': [role.name for role in member.roles if role.name != '@everyone']
                }
                members.append(member_info)
                member_count += 1
            
            # メンバーを名前順にソート
            members.sort(key=lambda x: x['display_name'].lower())
            
            # CSVファイルを作成
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'guild_members_{guild.name}_{current_time}.csv'
            filepath = f'/tmp/{filename}'
            
            # 統計情報を計算
            bot_count = sum(1 for m in members if m['is_bot'])
            human_count = len(members) - bot_count
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                # CSVライターを作成
                writer = csv.writer(f)
                
                # ヘッダー情報を書き込み
                writer.writerow(['# サーバー情報'])
                writer.writerow(['サーバー名', guild.name])
                writer.writerow(['サーバーID', guild.id])
                writer.writerow(['取得日時', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['総メンバー数', f'{len(members)}人'])
                writer.writerow(['人間', f'{human_count}人'])
                writer.writerow(['Bot', f'{bot_count}人'])
                writer.writerow([])  # 空行
                
                # CSVヘッダーを書き込み
                writer.writerow([
                    'No',
                    'ユーザーID',
                    'ユーザー名',
                    '表示名',
                    'ディスクリミネーター',
                    'アカウント作成日',
                    'サーバー参加日',
                    'Bot',
                    'ステータス',
                    'ロール'
                ])
                
                # メンバーデータを書き込み
                for i, member in enumerate(members, 1):
                    writer.writerow([
                        i,
                        member['id'],
                        member['name'],
                        member['display_name'],
                        member['discriminator'],
                        member['created_at'],
                        member['joined_at'],
                        'Yes' if member['is_bot'] else 'No',
                        member['status'],
                        ', '.join(member['roles']) if member['roles'] else 'なし'
                    ])
            
            # ファイルサイズをチェック
            file_size = os.path.getsize(filepath)
            
            # ファイルサイズが25MB以下かチェック（Discordの制限）
            if file_size > 25 * 1024 * 1024:  # 25MB
                await channel.send('メンバーリストが大きすぎます（25MB以上）。ファイルを分割する必要があります。')
                os.remove(filepath)
                return
            
            # ファイルをDiscordにアップロード
            with open(filepath, 'rb') as f:
                discord_file = discord.File(f, filename)
                await channel.send(
                    f'サーバー「{guild.name}」のメンバー一覧を取得しました！\n'
                    f'総メンバー数: {len(members)}人\n'
                    f'人間: {human_count}人 / Bot: {bot_count}人\n'
                    f'ファイルサイズ: {file_size:,}バイト',
                    file=discord_file
                )
            
            # 一時ファイルを削除
            os.remove(filepath)
            print(f'メンバーリストをアップロードしました: {filename}')
            
        except discord.Forbidden:
            await channel.send('エラー: メンバー情報を取得する権限がありません。Botに「メンバーを表示」権限を与えてください。')
        except Exception as e:
            await channel.send(f'メンバー一覧の取得中にエラーが発生しました: {str(e)}')
            print(f'メンバー取得エラー: {e}')

@bot.command(name='member_count')
async def member_count(ctx):
    """サーバーのメンバー数を表示するコマンド"""
    guild = ctx.guild
    if not guild:
        await ctx.send('このコマンドはサーバー内でのみ使用できます。')
        return
    
    try:
        member_count = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = member_count - bot_count
        
        await ctx.send(
            f'📊 サーバー「{guild.name}」の統計\n'
            f'総メンバー数: {member_count}人\n'
            f'オンライン: {online_members}人\n'
            f'人間: {human_count}人\n'
            f'Bot: {bot_count}人'
        )
    except Exception as e:
        await ctx.send(f'メンバー数の取得中にエラーが発生しました: {str(e)}')

if __name__ == '__main__':
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
    else:
        print('注意: このBotは「members」インテントが必要です。')
        print('Discord Developer Portalで「Server Members Intent」を有効にしてください。')
        bot.run(TOKEN)