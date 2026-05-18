import discord
from discord.ext import commands
from fastapi import FastAPI, Request, HTTPException
import uvicorn
import asyncio
import os
from dotenv import load_dotenv

# Import our AI Brain
import groq_agent 

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))

# --- 1. Initialize Discord Bot ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 2. Initialize FastAPI ---
app = FastAPI(title="Retention Butler Webhook Server")

# --- 3. FastAPI Webhook Endpoint (For Whop) ---
@app.post("/whop/webhook")
async def whop_webhook(request: Request):
    """Listens for payment events from Whop"""
    try:
        payload = await request.json()
        
        # --- DEBUG: Print the raw data so we can see what Whop is sending ---
        print(f"DEBUG: Received Webhook Data: {payload}")
        
        action = payload.get("action")
        
        # Whop sends IDs in different places depending on the event. 
        # This code checks all common spots:
        discord_user_id = (
            payload.get("discord_id") or 
            payload.get("discord_user_id") or 
            payload.get("user", {}).get("discord_id")
        )
        
        if not discord_user_id:
            print("DEBUG: Could not find a Discord ID in this specific payload.")
            # If it's just a test ping from Whop, we return success so Whop is happy
            return {"status": "success", "message": "Test received, but no Discord ID found."}

        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print(f"DEBUG: Guild {GUILD_ID} not found.")
            return {"status": "error", "message": "Guild not found"}

        try:
            member = await guild.fetch_member(int(discord_user_id))
        except Exception as e:
            print(f"DEBUG: Could not find user {discord_user_id} in Discord: {e}")
            return {"status": "error", "message": "User not in server"}

        if action == "payment_failed":
            await trigger_payment_rescue(member)
        elif action == "membership_created" or action == "membership.created":
            await trigger_vip_onboarding(member)
            
        return {"status": "success", "message": f"Processed {action} for {member.name}"}

    except Exception as e:
        print(f"CRITICAL WEBHOOK ERROR: {e}")
        return {"status": "error", "message": str(e)}

# --- 4. Discord Bot Logic ---
async def trigger_payment_rescue(member: discord.Member):
    try:
        await member.send(
            f"Hello {member.name}, I am the automated butler for the server.\n\n"
            "It looks like your most recent subscription renewal failed. "
            "To prevent you from losing access, I've secured a 3-day grace period for you. "
            "How can I assist you in updating your payment method today?"
        )
        print(f"DEBUG: Sent payment rescue DM to {member.name}")
    except discord.Forbidden:
        print(f"DEBUG: Could not send DM to {member.name}. Their DMs are closed.")

async def trigger_vip_onboarding(member: discord.Member):
    try:
        await member.send(
            f"Welcome to the VIP tier, {member.name}! I am your personal onboarding butler.\n\n"
            "I'm here to ensure you get immediate ROI from your membership. "
            "What is your #1 goal in the community right now?"
        )
        print(f"DEBUG: Sent VIP onboarding DM to {member.name}")
    except discord.Forbidden:
        print(f"DEBUG: Could not send DM to {member.name}. Their DMs are closed.")

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name} - The Butler is online.')

@bot.event
async def on_message(message):
    """Listens for user messages and replies using Groq AI"""
    
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # 1. Print every message the bot sees
    print(f"DEBUG: I just saw a message from {message.author}: {message.content}")

    # Check the context of the message
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions
    
    print(f"DEBUG: Is this a DM? {is_dm} | Was I mentioned? {is_mentioned}")
    print(f"DEBUG: {message.author}'s real ID is: {message.author.id}")

    # Respond IF it's a DM OR the bot is @mentioned
    if is_dm or is_mentioned:
        print("DEBUG: Condition met! Passing message to Groq AI...")
        
        # Show the "Bot is typing..." indicator in Discord
        async with message.channel.typing():
            
            # Clean up the text
            user_text = message.content.replace(f'<@{bot.user.id}>', '').strip()
            discord_id = str(message.author.id)

            # Pass to Groq API
            try:
                ai_response = await asyncio.to_thread(
                    groq_agent.process_user_message, 
                    discord_id, 
                    user_text
                )
                print(f"DEBUG: Groq API replied successfully.")
                
                # Send the AI response back to Discord
                await message.channel.send(ai_response)
                print("DEBUG: Message sent to Discord!")
            except Exception as e:
                print(f"DEBUG ERROR: Something failed during the Groq/DB step: {e}")
                
    else:
        print("DEBUG: I ignored the message because it wasn't a DM and I wasn't @mentioned.")

    # Process commands if you add any later
    await bot.process_commands(message)

# --- 5. Boot System ---
async def start_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    asyncio.create_task(start_fastapi())
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())