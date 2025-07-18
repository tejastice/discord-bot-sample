# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import openai
from datetime import datetime
import tempfile

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 対象のギルドとチャンネルID
TARGET_GUILD_ID = 1394139562028306644
TARGET_CHANNEL_ID = 1394203406574424104

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 文字起こし結果を保存するための辞書
transcription_files = {}

@bot.event
async def on_ready():
    print(f'{bot.user} が起動しました！')
    print(f'Bot ID: {bot.user.id}')
    print(f'対象ギルドID: {TARGET_GUILD_ID}')
    print(f'対象チャンネルID: {TARGET_CHANNEL_ID}')
    print('議事録作成ボット: 音声ファイルに👍でリアクション → 文字起こし、テキストファイルに❤️でリアクション → 議事録生成')

@bot.event
async def on_raw_reaction_add(payload):
    # Bot自身のリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    # 対象のギルドとチャンネルでない場合は無視
    if payload.guild_id != TARGET_GUILD_ID or payload.channel_id != TARGET_CHANNEL_ID:
        return
    
    try:
        # メッセージを取得
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        # 👍 リアクションの場合: 音声ファイルの文字起こし
        if str(payload.emoji) == '👍':
            await handle_transcription_request(channel, message)
        
        # ❤️ リアクションの場合: 文字起こしファイルから議事録生成
        elif str(payload.emoji) == '❤️':
            await handle_meeting_log_request(channel, message)
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        try:
            await channel.send(f"エラーが発生しました: {str(e)}")
        except:
            pass

async def handle_transcription_request(channel, message):
    """音声ファイルの文字起こし処理"""
    # 音声ファイルの添付ファイルがあるかチェック
    audio_attachments = []
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.aac', '.mp4', '.webm']
    
    for attachment in message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in audio_extensions):
            audio_attachments.append(attachment)
    
    if not audio_attachments:
        await channel.send("音声ファイルが見つかりませんでした。")
        return
    
    # 各音声ファイルを処理
    for attachment in audio_attachments:
        await process_audio_file(channel, attachment)

async def process_audio_file(channel, attachment):
    """音声ファイルを文字起こしする"""
    processing_msg = None
    temp_filename = None
    
    try:
        # ファイルサイズチェック (OpenAI APIの制限: 25MB)
        if attachment.size > 25 * 1024 * 1024:
            await channel.send(f"ファイル {attachment.filename} は25MBを超えているため処理できません。")
            return
        
        # 一時的な処理開始メッセージ
        processing_msg = await channel.send(f"🎵 {attachment.filename} の文字起こしを開始します...")
        
        # 音声ファイルをダウンロード
        audio_data = await attachment.read()
        
        # 一時ファイルに保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{attachment.filename}") as temp_file:
            temp_filename = temp_file.name
            temp_file.write(audio_data)
        
        # OpenAI Audio APIで文字起こし
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        with open(temp_filename, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ja"  # 日本語を指定
            )
        
        # 文字起こし結果を取得
        transcription_text = transcript.text
        
        if not transcription_text or transcription_text.strip() == "":
            await channel.send(f"❌ {attachment.filename} の文字起こしができませんでした。音声が認識できませんでした。")
            return
        
        # 結果をテキストファイルに保存
        output_content = f"""音声ファイル: {attachment.filename}
ファイルサイズ: {attachment.size:,} bytes
文字起こし実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
{'=' * 50}

【文字起こし結果】
{transcription_text}

{'=' * 50}
※ この文字起こしはOpenAI Whisperによって生成されました。
※ 議事録に変換するには、このファイルに❤️（ハートマーク）リアクションを押してください。
"""
        
        # 一時ファイルを作成してDiscordにアップロード
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as output_file:
            output_file.write(output_content)
            output_filename = output_file.name
        
        # Discordにファイルをアップロード
        with open(output_filename, 'rb') as f:
            discord_file = discord.File(f, filename=f"transcription_{attachment.filename}_{timestamp}.txt")
            sent_message = await channel.send(
                f"✅ {attachment.filename} の文字起こしが完了しました！\n"
                f"📄 文字起こし結果をファイルでダウンロードできます。\n"
                f"💡 このファイルに❤️リアクションを押すと議事録に変換されます。",
                file=discord_file
            )
        
        # 文字起こし結果を保存（議事録生成時に使用）
        transcription_files[sent_message.id] = {
            'transcription': transcription_text,
            'original_filename': attachment.filename,
            'timestamp': timestamp
        }
        
        # 処理開始メッセージを削除
        if processing_msg:
            await processing_msg.delete()
        
        # 一時ファイルのクリーンアップ
        try:
            if os.path.exists(output_filename):
                os.remove(output_filename)
        except Exception as e:
            print(f"出力ファイル削除エラー: {e}")
        
    except openai.OpenAIError as e:
        error_msg = f"OpenAI APIエラー: {str(e)}"
        await channel.send(error_msg)
        print(f"OpenAI APIエラー: {e}")
    except Exception as e:
        error_msg = f"文字起こし処理中にエラーが発生しました: {str(e)}"
        await channel.send(error_msg)
        print(f"文字起こしエラー: {e}")
    finally:
        # 一時ファイルのクリーンアップ
        try:
            if temp_filename and os.path.exists(temp_filename):
                os.remove(temp_filename)
        except Exception as e:
            print(f"一時ファイル削除エラー: {e}")
        
        # 処理開始メッセージが残っている場合は削除
        try:
            if processing_msg:
                await processing_msg.delete()
        except:
            pass

async def handle_meeting_log_request(channel, message):
    """テキストファイルから議事録を生成する"""
    # メッセージIDから文字起こし結果を取得
    if message.id not in transcription_files:
        # ファイルの内容を直接読み取って処理
        await process_text_file_for_meeting_log(channel, message)
        return
    
    # 保存されている文字起こし結果から議事録を生成
    transcription_data = transcription_files[message.id]
    await generate_meeting_log(channel, transcription_data['transcription'], transcription_data['original_filename'], transcription_data['timestamp'])

async def process_text_file_for_meeting_log(channel, message):
    """テキストファイルから内容を読み取って議事録を生成"""
    # テキストファイルの添付ファイルがあるかチェック
    text_attachments = []
    
    for attachment in message.attachments:
        if attachment.filename.lower().endswith('.txt'):
            text_attachments.append(attachment)
    
    if not text_attachments:
        await channel.send("テキストファイルが見つかりませんでした。")
        return
    
    # 各テキストファイルを処理
    for attachment in text_attachments:
        try:
            # ファイルサイズチェック (1MB制限)
            if attachment.size > 1024 * 1024:
                await channel.send(f"ファイル {attachment.filename} は1MBを超えているため処理できません。")
                continue
            
            # テキストファイルをダウンロード
            file_content = await attachment.read()
            text_content = file_content.decode('utf-8')
            
            # ファイル名とタイムスタンプを抽出
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 議事録を生成
            await generate_meeting_log(channel, text_content, attachment.filename, timestamp)
            
        except Exception as e:
            await channel.send(f"ファイル {attachment.filename} の処理中にエラーが発生しました: {str(e)}")

async def generate_meeting_log(channel, transcription_text, original_filename, timestamp):
    """文字起こし結果から議事録を生成"""
    processing_msg = None
    
    try:
        # 議事録生成開始メッセージ
        processing_msg = await channel.send(f"📝 {original_filename} の議事録を生成中...")
        
        # ChatGPT APIで議事録を生成
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        system_prompt = """あなたは議事録作成の専門家です。音声文字起こしの内容を元に、構造化された議事録を作成してください。

以下の形式で議事録を作成してください：

# 議事録

## 基本情報
- 日時: [推定または不明]
- 参加者: [発言者から推定、または不明]
- 議題: [内容から推定]

## 主要な議題・トピック
1. [議題1]
2. [議題2]
...

## 討議内容
### [トピック1]
- [要点1]
- [要点2]
...

### [トピック2]
- [要点1]
- [要点2]
...

## 決定事項
- [決定事項1]
- [決定事項2]
...

## アクションアイテム
- [担当者] [期限] [内容]
...

## 次回会議
- 日時: [記載があれば]
- 議題: [記載があれば]

## その他・補足事項
[必要に応じて]

---
※ この議事録は音声文字起こしを基に自動生成されました。詳細は元の文字起こしファイルをご確認ください。

注意事項：
- 文字起こしの内容を正確に反映し、推測で内容を追加しないでください
- 不明な部分は「不明」「推定」と明記してください
- 重要な発言や決定事項は漏らさないようにしてください
"""

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"以下の文字起こし内容を議事録に変換してください：\n\n{transcription_text}"}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        meeting_log = response.choices[0].message.content.strip()
        
        # 議事録をテキストファイルに保存
        meeting_log_content = f"""議事録生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
元ファイル: {original_filename}
{'=' * 60}

{meeting_log}

{'=' * 60}
※ この議事録はOpenAI GPT-4により自動生成されました。
※ 元の文字起こしファイルも併せてご確認ください。
"""
        
        # 一時ファイルを作成してDiscordにアップロード
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as output_file:
            output_file.write(meeting_log_content)
            output_filename = output_file.name
        
        # Discordにファイルをアップロード
        with open(output_filename, 'rb') as f:
            discord_file = discord.File(f, filename=f"meeting_log_{original_filename}_{timestamp}.txt")
            await channel.send(
                f"✅ 議事録の生成が完了しました！\n"
                f"📋 {original_filename} の議事録をファイルでダウンロードできます。",
                file=discord_file
            )
        
        # 処理開始メッセージを削除
        if processing_msg:
            await processing_msg.delete()
        
        # 一時ファイルのクリーンアップ
        try:
            if os.path.exists(output_filename):
                os.remove(output_filename)
        except Exception as e:
            print(f"出力ファイル削除エラー: {e}")
        
    except openai.OpenAIError as e:
        error_msg = f"OpenAI APIエラー: {str(e)}"
        await channel.send(error_msg)
        print(f"OpenAI APIエラー: {e}")
    except Exception as e:
        error_msg = f"議事録生成処理中にエラーが発生しました: {str(e)}"
        await channel.send(error_msg)
        print(f"議事録生成エラー: {e}")
    finally:
        # 処理開始メッセージが残っている場合は削除
        try:
            if processing_msg:
                await processing_msg.delete()
        except:
            pass

@bot.tree.command(name="meeting_log_help", description="議事録作成ボットの使い方を表示します")
async def meeting_log_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📝 議事録作成ボット - 使い方",
        description="音声ファイルから議事録を自動生成します",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="1️⃣ 文字起こし",
        value="• 音声ファイルを投稿\n• 👍 リアクションを押す\n• 文字起こしファイルが生成されます",
        inline=False
    )
    
    embed.add_field(
        name="2️⃣ 議事録生成",
        value="• 文字起こしファイルに ❤️ リアクションを押す\n• 構造化された議事録が生成されます",
        inline=False
    )
    
    embed.add_field(
        name="📋 対応ファイル形式",
        value="mp3, wav, m4a, flac, ogg, wma, aac, mp4, webm",
        inline=False
    )
    
    embed.add_field(
        name="⚠️ 制限事項",
        value="• 音声ファイル: 25MB以下\n• テキストファイル: 1MB以下\n• OpenAI API使用",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="meeting_log_status", description="議事録作成ボットの状態を確認します")
async def meeting_log_status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔍 議事録作成ボット - 状態",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="設定状況",
        value=f"OpenAI API: {'✅ 設定済み' if OPENAI_API_KEY else '❌ 未設定'}\n"
              f"対象ギルド: {TARGET_GUILD_ID}\n"
              f"対象チャンネル: {TARGET_CHANNEL_ID}",
        inline=False
    )
    
    embed.add_field(
        name="保存中の文字起こし",
        value=f"{len(transcription_files)}件",
        inline=False
    )
    
    embed.add_field(
        name="機能",
        value="• 音声文字起こし (Whisper-1)\n• 議事録生成 (GPT-4)\n• ファイル自動アップロード",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
        exit(1)
    
    if OPENAI_API_KEY is None:
        print('エラー: OPENAI_API_KEYが設定されていません')
        print('.envファイルにOPENAI_API_KEY=your_openai_api_keyを追加してください')
        exit(1)
    
    print('議事録作成ボットを起動します...')
    print('使い方:')
    print('1. 音声ファイルを投稿して👍リアクション → 文字起こし')
    print('2. 文字起こしファイルに❤️リアクション → 議事録生成')
    bot.run(TOKEN)