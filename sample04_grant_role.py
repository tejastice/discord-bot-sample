import discord
from discord.ext import commands
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True  # メンバー情報を取得・変更するために必要

bot = commands.Bot(command_prefix='!', intents=intents)

# ロール付与対象のユーザーIDリスト
TARGET_USER_IDS = [
    960439757345804308,
    399123569843372032,
    1394140956751564951
]

# 付与するロールID
TARGET_ROLE_ID = 1394560899800633344

@bot.event
async def on_ready():
    print(f'{bot.user}としてログインしました！')
    print('グッドマークのリアクションで指定されたユーザーにロールを付与します')
    print(f'対象ユーザー数: {len(TARGET_USER_IDS)}人')
    print(f'付与するロールID: {TARGET_ROLE_ID}')

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
        
        await channel.send('ロール付与処理を開始します...')
        
        try:
            # 付与するロールを取得
            target_role = guild.get_role(TARGET_ROLE_ID)
            if not target_role:
                await channel.send(f'エラー: ロールID {TARGET_ROLE_ID} が見つかりません。')
                return
            
            success_count = 0
            error_count = 0
            not_found_count = 0
            already_has_count = 0
            results = []
            
            # 各ユーザーにロールを付与
            for user_id in TARGET_USER_IDS:
                try:
                    # ギルドからメンバーを取得
                    member = guild.get_member(user_id)
                    if not member:
                        # キャッシュにない場合はfetchで取得を試行
                        try:
                            member = await guild.fetch_member(user_id)
                        except discord.NotFound:
                            results.append(f'❌ {user_id}: ユーザーがサーバーに見つかりません')
                            not_found_count += 1
                            continue
                    
                    # 既にロールを持っているかチェック
                    if target_role in member.roles:
                        results.append(f'⚠️ {member.display_name} ({user_id}): 既にロールを持っています')
                        already_has_count += 1
                        continue
                    
                    # ロールを付与
                    await member.add_roles(target_role, reason='Bot経由でのロール付与')
                    results.append(f'✅ {member.display_name} ({user_id}): ロール付与成功')
                    success_count += 1
                    
                except discord.Forbidden:
                    results.append(f'❌ {user_id}: 権限不足でロール付与できません')
                    error_count += 1
                except Exception as e:
                    results.append(f'❌ {user_id}: エラー - {str(e)}')
                    error_count += 1
            
            # 結果をテキストファイルに保存
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'role_grant_result_{current_time}.txt'
            filepath = f'/tmp/{filename}'
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f'ロール付与処理結果\n')
                f.write(f'実行日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'サーバー: {guild.name} ({guild.id})\n')
                f.write(f'付与ロール: {target_role.name} ({TARGET_ROLE_ID})\n')
                f.write('=' * 60 + '\n\n')
                
                f.write(f'処理結果サマリー:\n')
                f.write(f'  成功: {success_count}人\n')
                f.write(f'  既に保有: {already_has_count}人\n')
                f.write(f'  ユーザー未発見: {not_found_count}人\n')
                f.write(f'  エラー: {error_count}人\n')
                f.write(f'  合計: {len(TARGET_USER_IDS)}人\n\n')
                f.write('=' * 60 + '\n\n')
                
                f.write('詳細結果:\n')
                for result in results:
                    f.write(f'{result}\n')
            
            # 結果をDiscordに送信
            summary_message = (
                f'ロール付与処理が完了しました！\n'
                f'ロール: {target_role.name}\n'
                f'成功: {success_count}人 / 既に保有: {already_has_count}人\n'
                f'未発見: {not_found_count}人 / エラー: {error_count}人\n'
                f'合計: {len(TARGET_USER_IDS)}人'
            )
            
            # ファイルをアップロード
            with open(filepath, 'rb') as f:
                discord_file = discord.File(f, filename)
                await channel.send(summary_message, file=discord_file)
            
            # 一時ファイルを削除
            os.remove(filepath)
            print(f'ロール付与処理完了: 成功{success_count}人, エラー{error_count}人')
            
        except discord.Forbidden:
            await channel.send('エラー: ロールを管理する権限がありません。Botに「ロールの管理」権限を与えてください。')
        except Exception as e:
            await channel.send(f'ロール付与処理中にエラーが発生しました: {str(e)}')
            print(f'ロール付与エラー: {e}')

@bot.command(name='role_info')
async def role_info(ctx):
    """ロール付与対象の情報を表示するコマンド"""
    guild = ctx.guild
    if not guild:
        await ctx.send('このコマンドはサーバー内でのみ使用できます。')
        return
    
    try:
        target_role = guild.get_role(TARGET_ROLE_ID)
        if not target_role:
            await ctx.send(f'ロールID {TARGET_ROLE_ID} が見つかりません。')
            return
        
        await ctx.send(
            f'📊 ロール付与設定情報\n'
            f'対象ロール: {target_role.name} ({TARGET_ROLE_ID})\n'
            f'対象ユーザー数: {len(TARGET_USER_IDS)}人\n'
            f'ユーザーID一覧: {", ".join(map(str, TARGET_USER_IDS))}'
        )
    except Exception as e:
        await ctx.send(f'情報取得中にエラーが発生しました: {str(e)}')

if __name__ == '__main__':
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
    else:
        print('注意: このBotは「members」インテントと「ロールの管理」権限が必要です。')
        print('Discord Developer Portalで「Server Members Intent」を有効にしてください。')
        bot.run(TOKEN)