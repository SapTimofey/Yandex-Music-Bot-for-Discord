import torch
import discord
from transformers import GPTNeoForCausalLM, AutoTokenizer
from discord.ext import commands

tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neo-2.7B")
model = GPTNeoForCausalLM.from_pretrained("EleutherAI/gpt-neo-2.7B").to("cpu")

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

@client.command()
async def generate_text(ctx, *, prompt):
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to("cpu")
    output = model.generate(input_ids, max_length=8192, do_sample=True)
    text = tokenizer.decode(output[0], skip_special_tokens=True)
    await ctx.send(text)

client.run("MTA5MTA2MjkwNDM3NzMxMTM2Mw.GBr5WD.Ws3zyF8gjL5aklI4Ar05FuSAch8fjSfcRNOYII")
