# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

# 対象のギルドとチャンネルID
TARGET_GUILD_ID = 1394139562028306644
MEMO_CHANNEL_ID = 1395567281479745548

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} が起動しました！')
    print(f'Bot ID: {bot.user.id}')
    print(f'対象ギルドID: {TARGET_GUILD_ID}')
    print(f'メモチャンネルID: {MEMO_CHANNEL_ID}')
    print('グッドメモBot: メッセージに👍リアクション → メモチャンネルに転記')

@bot.event
async def on_raw_reaction_add(payload):
    # Bot自身のリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    # 👍 リアクションのみを処理
    if str(payload.emoji) != '👍':
        return
    
    # 対象のギルドでない場合は無視
    if payload.guild_id != TARGET_GUILD_ID:
        return
    
    # メモチャンネル自体のメッセージは無視（無限ループ防止）
    if payload.channel_id == MEMO_CHANNEL_ID:
        return
    
    try:
        # メッセージとユーザーを取得
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        memo_channel = bot.get_channel(MEMO_CHANNEL_ID)
        
        if not memo_channel:
            print(f"メモチャンネル ID {MEMO_CHANNEL_ID} が見つかりません")
            return
        
        # ユーザー情報の取得
        user = None
        guild = bot.get_guild(payload.guild_id)
        
        # ギルドメンバーから取得を試行
        if guild:
            user = guild.get_member(payload.user_id)
        
        # キャッシュから取得を試行
        if not user:
            user = bot.get_user(payload.user_id)
        
        # APIから直接取得を試行
        if not user:
            try:
                user = await bot.fetch_user(payload.user_id)
            except:
                pass
        
        # それでも取得できない場合は仮のユーザー情報を作成
        if not user:
            class FakeUser:
                def __init__(self, user_id):
                    self.id = user_id
                    self.display_name = f"退出済みユーザー({user_id})"
                    self.mention = f"<@{user_id}>"
            
            user = FakeUser(payload.user_id)
        
        # メッセージリンクを生成
        message_link = f"https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}"
        
        # 埋め込みメッセージを作成
        embed = discord.Embed(
            title="📌 グッドメモ",
            description=message.content if message.content else "*メッセージ内容なし*",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        # 元メッセージの情報を追加
        embed.add_field(
            name="投稿者",
            value=f"{message.author.mention} ({message.author.display_name})",
            inline=True
        )
        
        embed.add_field(
            name="チャンネル",
            value=f"<#{message.channel.id}>",
            inline=True
        )
        
        embed.add_field(
            name="リアクションユーザー",
            value=f"{user.mention} ({user.display_name})",
            inline=True
        )
        
        embed.add_field(
            name="元メッセージ",
            value=f"[メッセージリンク]({message_link})",
            inline=False
        )
        
        # 投稿日時を追加
        embed.add_field(
            name="投稿日時",
            value=message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            inline=True
        )
        
        # 添付ファイルがある場合は情報を追加
        if message.attachments:
            attachment_info = []
            for att in message.attachments:
                attachment_info.append(f"[{att.filename}]({att.url})")
            
            embed.add_field(
                name="添付ファイル",
                value="\n".join(attachment_info),
                inline=False
            )
        
        # Embedがある場合は情報を追加
        if message.embeds:
            embed_info = []
            for emb in message.embeds:
                if emb.title:
                    embed_info.append(f"**{emb.title}**")
                if emb.description:
                    embed_info.append(emb.description[:200] + "..." if len(emb.description) > 200 else emb.description)
            
            if embed_info:
                embed.add_field(
                    name="埋め込み内容",
                    value="\n".join(embed_info),
                    inline=False
                )
        
        # フッターを追加
        embed.set_footer(text=f"メモID: {message.id}")
        
        # 元メッセージに画像がある場合、最初の画像をサムネイルとして設定
        if message.attachments:
            for att in message.attachments:
                if any(att.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    embed.set_image(url=att.url)
                    break
        
        # メモチャンネルに送信
        await memo_channel.send(embed=embed)
        
        print(f"メモを転記しました: {message.author.display_name}の投稿 → #{memo_channel.name}")
        
    except Exception as e:
        print(f"メモ転記中にエラーが発生しました: {e}")
        try:
            error_channel = bot.get_channel(MEMO_CHANNEL_ID)
            if error_channel:
                await error_channel.send(f"⚠️ メモ転記エラー: {str(e)}")
        except:
            pass

@bot.tree.command(name="memo_info", description="グッドメモボットの情報を表示します")
async def memo_info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📌 グッドメモBot情報",
        description="メッセージに👍リアクションすると、メモチャンネルに転記されます",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="対象サーバー",
        value=f"ID: {TARGET_GUILD_ID}",
        inline=True
    )
    
    embed.add_field(
        name="メモチャンネル",
        value=f"<#{MEMO_CHANNEL_ID}>",
        inline=True
    )
    
    embed.add_field(
        name="使い方",
        value="任意のメッセージに👍リアクションを付けるだけ！",
        inline=False
    )
    
    embed.add_field(
        name="転記される情報",
        value="• メッセージ内容\n• 投稿者情報\n• チャンネル情報\n• メッセージリンク\n• 添付ファイル\n• 埋め込み内容",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sync_commands", description="スラッシュコマンドを同期します（管理者専用）")
async def sync_commands(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ このコマンドは管理者専用です", ephemeral=True)
        return
    
    try:
        synced = await bot.tree.sync()
        await interaction.response.send_message(f"✅ {len(synced)}個のコマンドを同期しました", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ コマンド同期エラー: {str(e)}", ephemeral=True)

@bot.event
async def on_error(event, *args, **kwargs):
    """エラーハンドリング"""
    print(f"エラーが発生しました: {event}")

if __name__ == "__main__":
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
        exit(1)
    
    print('グッドメモボットを起動します...')
    print('使い方: メッセージに👍リアクション → メモチャンネルに自動転記')
    print(f'対象サーバー: {TARGET_GUILD_ID}')
    print(f'メモチャンネル: {MEMO_CHANNEL_ID}')
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Bot起動エラー: {e}")