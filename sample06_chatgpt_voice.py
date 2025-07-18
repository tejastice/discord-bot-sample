import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import openai
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 対象のギルドとチャンネルID
TARGET_GUILD_ID = 1394139562028306644
TARGET_CHANNEL_ID = 1394203406574424104

@bot.event
async def on_ready():
    print(f'{bot.user} が起動しました！')
    print(f'Bot ID: {bot.user.id}')

@bot.event
async def on_raw_reaction_add(payload):
    # 👍 リアクションのみを処理
    if str(payload.emoji) != '👍':
        return
    
    # 対象のギルドとチャンネルでない場合は無視
    if payload.guild_id != TARGET_GUILD_ID or payload.channel_id != TARGET_CHANNEL_ID:
        return
    
    # Bot自身のリアクションは無視
    if payload.user_id == bot.user.id:
        return
    
    try:
        # メッセージを取得
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
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
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        try:
            await channel.send(f"エラーが発生しました: {str(e)}")
        except:
            pass

async def process_audio_file(channel, attachment):
    processing_msg = None
    temp_filename = None
    output_filename = None
    
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
        temp_filename = f"/tmp/{timestamp}_{attachment.filename}"
        with open(temp_filename, 'wb') as f:
            f.write(audio_data)
        
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
        output_filename = f"/tmp/transcription_{timestamp}.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(f"音声ファイル: {attachment.filename}\n")
            f.write(f"ファイルサイズ: {attachment.size:,} bytes\n")
            f.write(f"文字起こし実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write("【文字起こし結果】\n")
            f.write(transcription_text)
            f.write("\n\n")
            f.write("=" * 50 + "\n")
            f.write("※ この文字起こしはOpenAI Whisperによって生成されました。\n")
        
        # Discordにファイルをアップロード
        with open(output_filename, 'rb') as f:
            discord_file = discord.File(f, filename=f"transcription_{attachment.filename}_{timestamp}.txt")
            await channel.send(
                f"✅ {attachment.filename} の文字起こしが完了しました！\n"
                f"📄 文字起こし結果をファイルでダウンロードできます。",
                file=discord_file
            )
        
        # 処理開始メッセージを削除
        if processing_msg:
            await processing_msg.delete()
        
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
        
        try:
            if output_filename and os.path.exists(output_filename):
                os.remove(output_filename)
        except Exception as e:
            print(f"出力ファイル削除エラー: {e}")
        
        # 処理開始メッセージが残っている場合は削除
        try:
            if processing_msg:
                await processing_msg.delete()
        except:
            pass

if __name__ == "__main__":
    bot.run(TOKEN)