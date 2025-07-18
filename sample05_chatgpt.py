import discord
from discord.ext import commands
import os
import openai
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TARGET_CHANNEL_ID = 1394203406574424104  # ChatGPTが応答する対象チャンネル

# OpenAI クライアントを初期化
openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user}としてログインしました！')
    print(f'チャンネルID {TARGET_CHANNEL_ID} でChatGPTが応答します')

@bot.event
async def on_message(message):
    # ボット自身のメッセージは無視
    if message.author == bot.user:
        return
    
    # 対象チャンネルでのメッセージのみ処理
    if message.channel.id == TARGET_CHANNEL_ID:
        # "thinking..." リアクションを追加
        await message.add_reaction('🤔')
        
        try:
            # ChatGPTに送信するメッセージを準備
            user_message = message.content
            
            # OpenAI API呼び出し
            response = await get_chatgpt_response(user_message, message.author.display_name)
            
            # レスポンスが長すぎる場合は分割
            if len(response) > 2000:
                # Discordの2000文字制限に対応
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await message.reply(chunk)
                    else:
                        await message.channel.send(chunk)
            else:
                await message.reply(response)
            
            # "thinking..." リアクションを削除して完了リアクション追加
            await message.remove_reaction('🤔', bot.user)
            await message.add_reaction('✅')
            
        except Exception as e:
            await message.reply(f'エラーが発生しました: {str(e)}')
            await message.remove_reaction('🤔', bot.user)
            await message.add_reaction('❌')
            print(f'ChatGPT API エラー: {e}')
    
    # コマンド処理
    await bot.process_commands(message)

async def get_chatgpt_response(user_message, username):
    """ChatGPT APIを呼び出して応答を取得"""
    try:
        # 最新のOpenAI API形式（responses.create）
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # システムプロンプトとユーザーメッセージを組み合わせて入力を作成
        system_prompt = f"あなたは元気いっぱいの男の子の少年です！{username}さんと楽しくお話しするのが大好きです。明るく元気で好奇心旺盛な少年として、日本語で楽しく会話してください。「だよ！」「すごいね！」「わーい！」などの元気な言葉遣いを使って、簡潔で分かりやすい回答をしてください。"
        combined_input = f"{system_prompt}\n\nユーザー: {user_message}"
        
        response = client.responses.create(
            model="gpt-4.1",
            input=combined_input
        )
        
        return response.output_text.strip()
        
    except Exception as e:
        # フォールバック: 従来のchat.completions.create形式（gpt-4使用）
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": f"あなたは元気いっぱいの男の子の少年です！{username}さんと楽しくお話しするのが大好きです。明るく元気で好奇心旺盛な少年として、日本語で楽しく会話してください。「だよ！」「すごいね！」「わーい！」などの元気な言葉遣いを使って、簡潔で分かりやすい回答をしてください。"
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
                max_tokens=500,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as fallback_error:
            print(f'OpenAI APIエラー (フォールバック): {fallback_error}')
            raise Exception(f"ChatGPT API呼び出しに失敗しました: {str(e)}")

@bot.command(name='chatgpt_test')
async def chatgpt_test(ctx, *, message):
    """ChatGPTのテストコマンド"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.send('このコマンドは指定されたチャンネルでのみ使用できます。')
        return
    
    try:
        response = await get_chatgpt_response(message, ctx.author.display_name)
        await ctx.send(f'**テスト応答:**\n{response}')
    except Exception as e:
        await ctx.send(f'テスト中にエラーが発生しました: {str(e)}')

@bot.command(name='chatgpt_status')
async def chatgpt_status(ctx):
    """ChatGPTの設定状況を確認"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.send('このコマンドは指定されたチャンネルでのみ使用できます。')
        return
    
    status_message = (
        f'🤖 ChatGPT Discord Bot 設定状況\n'
        f'対象チャンネル: {TARGET_CHANNEL_ID}\n'
        f'OpenAI API設定: {"✅ 設定済み" if OPENAI_API_KEY else "❌ 未設定"}\n'
        f'メインモデル: gpt-4.1 (最新)\n'
        f'フォールバックモデル: gpt-4\n'
        f'API形式: responses.create (最新)'
    )
    
    await ctx.send(status_message)

if __name__ == '__main__':
    if TOKEN is None:
        print('エラー: DISCORD_TOKENが設定されていません')
        print('.envファイルにDISCORD_TOKEN=your_bot_tokenを追加してください')
        exit(1)
    
    if OPENAI_API_KEY is None:
        print('エラー: OPENAI_API_KEYが設定されていません')
        print('.envファイルにOPENAI_API_KEY=your_openai_api_keyを追加してください')
        exit(1)
    
    print('ChatGPT Discord Botを起動します...')
    print(f'対象チャンネルID: {TARGET_CHANNEL_ID}')
    print('注意: OpenAI APIキーが正しく設定されていることを確認してください。')
    bot.run(TOKEN)