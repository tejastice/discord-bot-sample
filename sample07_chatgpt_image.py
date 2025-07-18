import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import openai
import base64
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
        
        # 画像ファイルの添付ファイルがあるかチェック
        image_attachments = []
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in image_extensions):
                image_attachments.append(attachment)
        
        if not image_attachments:
            await channel.send("画像ファイルが見つかりませんでした。")
            return
        
        # 各画像ファイルを処理
        for attachment in image_attachments:
            await process_image_file(channel, attachment)
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        try:
            await channel.send(f"エラーが発生しました: {str(e)}")
        except:
            pass

async def process_image_file(channel, attachment):
    processing_msg = None
    output_filename = None
    
    try:
        # ファイルサイズチェック (50MB制限)
        if attachment.size > 50 * 1024 * 1024:
            await channel.send(f"ファイル {attachment.filename} は50MBを超えているため処理できません。")
            return
        
        # 一時的な処理開始メッセージ
        processing_msg = await channel.send(f"📸 {attachment.filename} の文字起こしを開始します...")
        
        # 画像ファイルをダウンロード
        image_data = await attachment.read()
        
        # Base64エンコーディング
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # OpenAI Vision APIで画像の文字起こし
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "この画像に含まれている文字をすべて読み取って、正確にテキストとして出力してください。画像に文字が含まれていない場合は「この画像には文字が含まれていません」と回答してください。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        # 文字起こし結果を取得
        ocr_text = response.choices[0].message.content
        
        if not ocr_text or ocr_text.strip() == "":
            await channel.send(f"❌ {attachment.filename} の文字起こしができませんでした。")
            return
        
        # 結果をテキストファイルに保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"/tmp/ocr_result_{timestamp}.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(f"画像ファイル: {attachment.filename}\n")
            f.write(f"ファイルサイズ: {attachment.size:,} bytes\n")
            f.write(f"文字起こし実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write("【文字起こし結果】\n")
            f.write(ocr_text)
            f.write("\n\n")
            f.write("=" * 50 + "\n")
            f.write("※ この文字起こしはOpenAI Vision APIによって生成されました。\n")
        
        # Discordにファイルをアップロード
        with open(output_filename, 'rb') as f:
            discord_file = discord.File(f, filename=f"ocr_result_{attachment.filename}_{timestamp}.txt")
            await channel.send(
                f"✅ **{attachment.filename}** の文字起こしが完了しました！\n"
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
        error_msg = f"画像の文字起こし処理中にエラーが発生しました: {str(e)}"
        await channel.send(error_msg)
        print(f"画像文字起こしエラー: {e}")
    finally:
        # 一時ファイルのクリーンアップ
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