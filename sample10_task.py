# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

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

class TaskManager:
    """タスク管理クラス"""
    
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
    
    def create_task(self, title):
        """新しいタスクを作成"""
        if not self.connection or self.connection.closed:
            return None
        
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO tasks (title, completed) VALUES (%s, %s) RETURNING id"
            cursor.execute(query, (title, False))
            task_id = cursor.fetchone()[0]
            self.connection.commit()
            cursor.close()
            print(f"タスクを作成しました: ID={task_id}, タイトル={title}")
            return task_id
        except psycopg2.Error as e:
            print(f"タスク作成エラー: {e}")
            return None
    
    def get_incomplete_tasks(self):
        """未完了のタスクのみを取得"""
        if not self.connection or self.connection.closed:
            return []
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            query = "SELECT id, title, completed FROM tasks WHERE completed = FALSE ORDER BY id ASC"
            cursor.execute(query)
            tasks = cursor.fetchall()
            cursor.close()
            return tasks
        except psycopg2.Error as e:
            print(f"タスク取得エラー: {e}")
            return []
    
    def toggle_task_completion(self, task_id):
        """タスクの完了状態を切り替え"""
        if not self.connection or self.connection.closed:
            return False
        
        try:
            cursor = self.connection.cursor()
            # 現在の状態を取得
            cursor.execute("SELECT completed FROM tasks WHERE id = %s", (task_id,))
            result = cursor.fetchone()
            if not result:
                cursor.close()
                return False
            
            # 状態を反転
            new_status = not result[0]
            cursor.execute("UPDATE tasks SET completed = %s WHERE id = %s", (new_status, task_id))
            self.connection.commit()
            cursor.close()
            
            status_text = "完了" if new_status else "未完了"
            print(f"タスクID={task_id}を{status_text}に変更しました")
            return True
        except psycopg2.Error as e:
            print(f"タスク更新エラー: {e}")
            return False

# タスクマネージャーのインスタンス作成
task_manager = TaskManager(DB_CONFIG)

@bot.event
async def on_ready():
    print(f'{bot.user} が起動しました！')
    print(f'Bot ID: {bot.user.id}')
    print(f'対象ギルドID: {TARGET_GUILD_ID}')
    
    # データベース接続
    if task_manager.connect():
        print("タスク管理Bot準備完了")
    else:
        print("警告: データベースに接続できませんでした")
    
    print('📝 リアクション式タスク管理Bot')
    print('👍 = タスク作成')
    print('❤️ = 未完了タスク一覧表示')
    print('✅ = タスク完了切り替え')

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
        
        # 👍リアクション: タスク作成
        if str(payload.emoji) == '👍':
            await handle_task_creation(channel, payload)
        
        # ❤️リアクション: タスク一覧表示
        elif str(payload.emoji) == '❤️':
            await handle_task_list_display(channel, payload)
        
        # ✅リアクション: タスク完了切り替え
        elif str(payload.emoji) == '✅':
            await handle_task_completion_toggle(channel, payload)
            
    except Exception as e:
        print(f"リアクション処理中にエラー: {e}")

async def handle_task_creation(channel, payload):
    """👍リアクションによるタスク作成処理"""
    try:
        # 元のメッセージを取得
        message = await channel.fetch_message(payload.message_id)
        
        # メッセージ内容をタスクタイトルとして使用
        if not message.content:
            await channel.send("📝 メッセージに内容がないため、タスクを作成できません", delete_after=5)
            return
        
        # タスクを作成
        task_id = task_manager.create_task(message.content)
        if task_id:
            embed = discord.Embed(
                title="📝 タスク作成完了",
                description=f"**タスク#{task_id}** を作成しました",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="内容",
                value=message.content[:200] + "..." if len(message.content) > 200 else message.content,
                inline=False
            )
            embed.set_footer(text=f"作成者: {message.author.display_name}")
            
            await channel.send(embed=embed, delete_after=10)
        else:
            await channel.send("❌ タスクの作成に失敗しました", delete_after=5)
            
    except Exception as e:
        print(f"タスク作成エラー: {e}")
        await channel.send("❌ タスク作成中にエラーが発生しました", delete_after=5)

async def handle_task_list_display(channel, payload):
    """❤️リアクションによるタスク一覧表示処理"""
    try:
        # 未完了タスクのみを取得
        tasks = task_manager.get_incomplete_tasks()
        
        if not tasks:
            embed = discord.Embed(
                title="📋 未完了タスク一覧",
                description="現在未完了のタスクはありません🎉",
                color=discord.Color.green()
            )
            await channel.send(embed=embed, delete_after=10)
            return
        
        # 各タスクを個別のメッセージとして投稿
        await channel.send(f"📋 **未完了タスク一覧** ({len(tasks)}件)")
        
        for task in tasks:
            embed = discord.Embed(
                title=f"📝 タスク#{task['id']}",
                description=task['title'],
                color=discord.Color.blue()
            )
            embed.add_field(
                name="状態",
                value="未完了",
                inline=True
            )
            embed.set_footer(text=f"ID: {task['id']} | ✅で完了にする")
            
            # メッセージを送信し、✅リアクションを追加
            sent_message = await channel.send(embed=embed)
            await sent_message.add_reaction('✅')
            
    except Exception as e:
        print(f"タスク一覧表示エラー: {e}")
        await channel.send("❌ タスク一覧の表示中にエラーが発生しました", delete_after=5)

async def handle_task_completion_toggle(channel, payload):
    """✅リアクションによるタスク完了切り替え処理"""
    try:
        # Botが送信したメッセージかチェック
        message = await channel.fetch_message(payload.message_id)
        if message.author.id != bot.user.id:
            return  # Botのメッセージでない場合は無視
        
        # メッセージのEmbedからタスクIDを抽出
        if not message.embeds:
            return
        
        embed = message.embeds[0]
        if not embed.title or "タスク#" not in embed.title:
            return
        
        try:
            # タイトルからタスクIDを抽出 (例: "✅ タスク#123" → 123)
            task_id_str = embed.title.split("タスク#")[1].split()[0]
            task_id = int(task_id_str)
        except (IndexError, ValueError):
            return
        
        # タスクの完了状態を切り替え
        if task_manager.toggle_task_completion(task_id):
            # 成功メッセージを送信
            await channel.send(f"✅ タスク#{task_id} の状態を切り替えました", delete_after=5)
            
            # 新しいタスク一覧を表示
            await handle_task_list_display(channel, payload)
        else:
            await channel.send(f"❌ タスク#{task_id} の状態切り替えに失敗しました", delete_after=5)
            
    except Exception as e:
        print(f"タスク完了切り替えエラー: {e}")
        await channel.send("❌ タスク状態の切り替え中にエラーが発生しました", delete_after=5)

@bot.event
async def on_disconnect():
    """Bot切断時の処理"""
    print("Botが切断されました")
    task_manager.disconnect()

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
    
    print('📝 リアクション式タスク管理Botを起動します...')
    print('使い方:')
    print('  👍 メッセージにリアクション → タスク作成')
    print('  ❤️ メッセージにリアクション → 未完了タスク一覧表示')
    print('  ✅ Botのタスクメッセージにリアクション → 完了切り替え')
    print(f'対象サーバー: {TARGET_GUILD_ID}')
    print(f'データベース: {DB_CONFIG["host"]}')
    
    try:
        bot.run(TOKEN)
    finally:
        # Bot終了時にデータベース接続を切断
        task_manager.disconnect()