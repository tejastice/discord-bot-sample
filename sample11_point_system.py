# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

# Supabase PostgreSQL データベース設定
DB_CONFIG = {
    'host': os.getenv('SUPABASE_HOST'),
    'database': os.getenv('SUPABASE_DATABASE'),
    'user': os.getenv('SUPABASE_USER'),
    'password': os.getenv('SUPABASE_PASSWORD'),
    'port': int(os.getenv('SUPABASE_PORT', 5432)),
    'sslmode': 'require'
}

# 対象のギルドID
TARGET_GUILD_ID = 1394139562028306644

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

class PointSystem:
    """ポイントシステム管理クラス"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
    
    def connect(self):
        """データベースに接続"""
        try:
            self.connection = psycopg2.connect(**self.config)
            print(f"Supabase PostgreSQLに接続しました: {self.config['host']}")
            return True
        except psycopg2.Error as e:
            print(f"データベース接続エラー: {e}")
            return False
    
    def disconnect(self):
        """データベース接続を切断"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            print("データベース接続を切断しました")
    
    def grant_point(self, giver_user_id, receiver_user_id, message_id):
        """ポイントを付与（重複チェック付き）"""
        if not self.connection or self.connection.closed:
            return False, "データベース接続エラー"
        
        # 自分に自分でポイントを付与することを防ぐ
        if giver_user_id == receiver_user_id:
            return False, "自分にはポイントを付与できません"
        
        try:
            cursor = self.connection.cursor()
            
            # 重複チェック（同じメッセージに同じユーザーからのポイント付与があるか）
            cursor.execute(
                "SELECT 1 FROM point_grants WHERE message_id = %s AND giver_user_id = %s",
                (message_id, giver_user_id)
            )
            if cursor.fetchone():
                cursor.close()
                return False, "このメッセージには既にポイントを付与済みです"
            
            # ポイント付与履歴を記録
            cursor.execute(
                "INSERT INTO point_grants (message_id, giver_user_id, receiver_user_id) VALUES (%s, %s, %s)",
                (message_id, giver_user_id, receiver_user_id)
            )
            
            # ユーザーポイントテーブルを更新（UPSERT）
            cursor.execute("""
                INSERT INTO user_points (user_id, points, updated_at) 
                VALUES (%s, 1, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    points = user_points.points + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (receiver_user_id,))
            
            # 更新後のポイント数を取得
            cursor.execute("SELECT points FROM user_points WHERE user_id = %s", (receiver_user_id,))
            new_points = cursor.fetchone()[0]
            
            self.connection.commit()
            cursor.close()
            
            print(f"ポイント付与: {giver_user_id} → {receiver_user_id} (合計: {new_points}pt)")
            return True, new_points
            
        except psycopg2.Error as e:
            print(f"ポイント付与エラー: {e}")
            if self.connection:
                self.connection.rollback()
            return False, "ポイント付与に失敗しました"
    
    def get_user_points(self, user_id):
        """ユーザーの現在ポイントを取得"""
        if not self.connection or self.connection.closed:
            return 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT points FROM user_points WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else 0
            
        except psycopg2.Error as e:
            print(f"ポイント取得エラー: {e}")
            return 0

# ポイントシステムのインスタンス作成
point_system = PointSystem(DB_CONFIG)

@bot.event
async def on_ready():
    print(f'{bot.user} が起動しました！')
    print(f'Bot ID: {bot.user.id}')
    print(f'対象ギルドID: {TARGET_GUILD_ID}')
    
    # データベース接続
    if point_system.connect():
        print("ポイントシステムBot準備完了")
    else:
        print("警告: データベースに接続できませんでした")
    
    print('💎 リアクション式ポイントシステムBot')
    print('👍 = ポイント付与（投稿者に1pt）')
    print('❤️ = ポイント確認（自分の現在pt）')

@bot.event
async def on_raw_reaction_add(payload):
    # Bot自身のリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    # 対象のギルドでない場合は無視
    if payload.guild_id != TARGET_GUILD_ID:
        return
    
    try:
        # チャンネルとメッセージを取得
        channel = bot.get_channel(payload.channel_id)
        if not channel:
            return
        
        # 👍リアクション: ポイント付与
        if str(payload.emoji) == '👍':
            await handle_point_grant(channel, payload)
        
        # ❤️リアクション: ポイント確認
        elif str(payload.emoji) == '❤️':
            await handle_point_check(channel, payload)
            
    except Exception as e:
        print(f"リアクション処理中にエラー: {e}")

async def handle_point_grant(channel, payload):
    """👍リアクションによるポイント付与処理"""
    try:
        # 元のメッセージを取得
        message = await channel.fetch_message(payload.message_id)
        
        # Bot自身のメッセージには付与しない
        if message.author.id == bot.user.id:
            return
        
        # ギルドメンバー情報を取得
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            print(f"ギルドが見つかりません: {payload.guild_id}")
            return
            
        # メンバー情報を取得（管理者など特権ユーザーも含む）
        try:
            giver = await guild.fetch_member(payload.user_id)
        except discord.NotFound:
            print(f"付与者のメンバー情報を取得できません: {payload.user_id}")
            giver = None
        except discord.Forbidden:
            # 権限不足の場合はget_memberで試す
            giver = guild.get_member(payload.user_id)
            
        try:
            receiver = await guild.fetch_member(message.author.id)
        except discord.NotFound:
            print(f"受信者のメンバー情報を取得できません: {message.author.id}")
            receiver = None
        except discord.Forbidden:
            # 権限不足の場合はget_memberで試す
            receiver = guild.get_member(message.author.id)
        
        # どちらかのメンバー情報が取得できない場合はログ出力して処理続行
        if not giver:
            print(f"警告: 付与者のメンバー情報が取得できませんでした（ID: {payload.user_id}）")
        if not receiver:
            print(f"警告: 受信者のメンバー情報が取得できませんでした（ID: {message.author.id}）")
            # 受信者情報が必須なので、取得できない場合は処理を停止
            return
        
        # ポイント付与実行
        success, result = point_system.grant_point(
            payload.user_id, 
            message.author.id, 
            payload.message_id
        )
        
        if success:
            # 成功時のEmbed
            embed = discord.Embed(
                title="👍 ポイント付与完了",
                description=f"**{receiver.display_name}** さんに1ポイント付与しました！",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="現在の合計ポイント",
                value=f"💎 {result}pt",
                inline=True
            )
            embed.set_thumbnail(url=receiver.display_avatar.url)
            if giver:
                embed.set_footer(
                    text=f"付与者: {giver.display_name}",
                    icon_url=giver.display_avatar.url
                )
            else:
                embed.set_footer(text=f"付与者ID: {payload.user_id}")
            
            await channel.send(embed=embed, delete_after=10)
        else:
            # 失敗時のメッセージ（重複など）
            if "既に" in result:
                return  # 重複の場合は静かに無視
            
            embed = discord.Embed(
                title="❌ ポイント付与エラー",
                description=result,
                color=discord.Color.red()
            )
            await channel.send(embed=embed, delete_after=5)
            
    except Exception as e:
        print(f"ポイント付与エラー: {e}")

async def handle_point_check(channel, payload):
    """❤️リアクションによるポイント確認処理"""
    try:
        # ギルドメンバー情報を取得
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            print(f"ギルドが見つかりません: {payload.guild_id}")
            return
            
        # メンバー情報を取得（管理者など特権ユーザーも含む）
        try:
            user = await guild.fetch_member(payload.user_id)
        except discord.NotFound:
            print(f"ユーザーのメンバー情報を取得できません: {payload.user_id}")
            user = None
        except discord.Forbidden:
            # 権限不足の場合はget_memberで試す
            user = guild.get_member(payload.user_id)
        
        if not user:
            print(f"警告: ユーザーのメンバー情報が取得できませんでした（ID: {payload.user_id}）")
            return
        
        # ユーザーの現在ポイントを取得
        current_points = point_system.get_user_points(payload.user_id)
        
        # ポイント確認のEmbed
        embed = discord.Embed(
            title="💎 ポイント確認",
            description=f"**{user.display_name}** さんの現在ポイント",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="現在のポイント",
            value=f"💎 {current_points}pt",
            inline=False
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"ユーザーID: {user.id}")
        
        await channel.send(embed=embed, delete_after=10)
        
    except Exception as e:
        print(f"ポイント確認エラー: {e}")

@bot.event
async def on_disconnect():
    """Bot切断時の処理"""
    print("Botが切断されました")
    point_system.disconnect()

@bot.event
async def on_error(event, *args, **kwargs):
    """エラーハンドリング"""
    print(f"エラーが発生しました: {event}")

if __name__ == "__main__":
    # 必要な環境変数チェック
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
        exit(1)
    
    # Supabase設定チェック
    required_env_vars = ['SUPABASE_HOST', 'SUPABASE_DATABASE', 'SUPABASE_USER', 'SUPABASE_PASSWORD']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f'エラー: 以下のSupabase設定が不足しています: {", ".join(missing_vars)}')
        print('.envファイルに以下を追加してください:')
        print('SUPABASE_HOST=your-project.supabase.co')
        print('SUPABASE_DATABASE=postgres')
        print('SUPABASE_USER=postgres')
        print('SUPABASE_PASSWORD=your-password')
        print('SUPABASE_PORT=5432')
        exit(1)
    
    print('💎 リアクション式ポイントシステムBotを起動します...')
    print('使い方:')
    print('  👍 メッセージにリアクション → 投稿者に1ポイント付与')
    print('  ❤️ メッセージにリアクション → 自分の現在ポイント確認')
    print(f'対象サーバー: {TARGET_GUILD_ID}')
    print(f'データベース: {DB_CONFIG["host"]}')
    
    try:
        bot.run(TOKEN)
    finally:
        # Bot終了時にデータベース接続を切断
        point_system.disconnect()