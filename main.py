import os 
import yaml
import json
import discord
from tasksio import TaskPool
from discord.ext import commands
import requests

config = yaml.safe_load(open('config.yml', "r"))
prefix = config['prefix']
token = config['token']
fromadd = config['from_address']
prvtkey = config['prvt_key']

def clear_console():
  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')

clear_console()

bot = commands.Bot(command_prefix=prefix, self_bot=True, case_insensitive=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return 
    
def load_ar():
  try:
    with open('ar.json', 'r') as file:
      return json.load(file)
  except FileNotFoundError:
    return {}


def save_ar(data):
  with open('ar.json', 'w') as file:
    json.dump(data, file, indent=4)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        ar = load_ar()
        content = message.content.lower()

        if content in ar:
            response = ar[content]
            await message.channel.send(response)
            await message.delete()
    await bot.process_commands(message)


@bot.command()
async def ping(ctx):
  await ctx.send(f'>>> **Latency: {bot.latency*1000:.2f}ms**')
  await ctx.message.delete()
  
@bot.command()
async def addar(ctx, trigger, *, response):
  ar = load_ar()
  ar[trigger] = response
  save_ar(ar)
  await ctx.send(f'>>> **__Autoresponder added__: `{trigger}` -> `{response}`**',
                 delete_after=10)
  await ctx.message.delete()

@bot.command()
async def removear(ctx, trigger):
  ar = load_ar()
  if trigger in ar:
    del ar[trigger]
    save_ar(ar)
    await ctx.send(f'>>> **__Autoresponder removed__: `{trigger}`**', delete_after=10)
    await ctx.message.delete()
  else:
    await ctx.send('>>> Autoresponder not found.', delete_after=5)
    await ctx.message.delete()

@bot.command()
async def listar(ctx):
  ar = load_ar()
  if ar:
    response = '__Autoresponders__:\n'
    for trigger, response_text in ar.items():
      response += f'{trigger} -> `{response_text}`\n'
    await ctx.send(f">>> **{response}**", delete_after=10)
    await ctx.message.delete()
  else:
    await ctx.send('>>> No autoresponders found.', delete_after=5)
    await ctx.message.delete()


async def spamm(_self, msg):
  await _self.send(msg)
@bot.command()
async def spam(ctx, amount: int, *msg):
  await ctx.message.delete()
  msg = " ".join(msg)
  async with TaskPool(1_000) as pool:
    for i in range(amount):
      await pool.put(spamm(ctx, msg))


@bot.command(aliases=['pltc', 'ltcprice', "ltc"])
async def price(ctx):
  url = 'https://api.coingecko.com/api/v3/coins/litecoin'
  response = requests.get(url)
  try:
    if response.status_code == 200:
      data = response.json()
      price = data['market_data']['current_price']['usd']
      await ctx.send(f">>> **Current LTC price: __${price:.2f}__**", delete_after=10)
      await ctx.message.delete()
  except Exception as e:
        print(e)
        await ctx.message.delete()


@bot.command()
async def help(ctx):
  command_list = [f"{command.name}" for command in bot.commands]
  command_list.sort()
  command_list_str = '\n'.join(command_list)
  await ctx.send(f'>>> **__Commands__\n\n{command_list_str}**',
                 delete_after=30)
  await ctx.message.delete()

@bot.command(aliases=["bal"])
async def getbal(ctx, ltcaddress: str = None):
  if ltcaddress is None:
    return await ctx.send(">>> Please provide a LTC address.", delete_after=5)
  response = requests.get(
      f'https://api.blockcypher.com/v1/ltc/main/addrs/{ltcaddress}/balance')
  if response.status_code != 200:
    if response.status_code == 400:
      await ctx.send(">>> Invalid LTC address.", delete_after=10)
    else:
      await ctx.send(
          f">>> Failed to retrieve balance. Error {response.status_code}. Please try again later",
          delete_after=5)
    return
  data = response.json()
  balance = data['balance'] / 10**8
  total_balance = data['total_received'] / 10**8
  unconfirmed_balance = data['unconfirmed_balance'] / 10**8
  cg_response = requests.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd'
  )
  if cg_response.status_code != 200:
    await ctx.send(
        f"Failed to retrieve the current price of LTC. Error {cg_response.status_code}. Please try again later",
        delete_after=5)
    return
  usd_price = cg_response.json()['litecoin']['usd']
  usd_balance = balance * usd_price
  usd_total_balance = total_balance * usd_price
  usd_unconfirmed_balance = unconfirmed_balance * usd_price
  message = f"__LTC Address__: `{ltcaddress}`\n"
  message += f"__Current LTC__ ~ `${usd_balance:.2f}`\n"
  message += f"__Total LTC Received__ ~ `${usd_total_balance:.2f}`\n"
  message += f"__Unconfirmed LTC__ ~ `${usd_unconfirmed_balance:.2f}`"
  await ctx.send(f">>> **{message}**", delete_after=30)
  await ctx.message.delete()

    
@bot.command()
async def status(ctx, type=None, *, text=None):
  if not type:
    await ctx.send("Error! Status type is required.", delete_after=10)
  if not text:
    await ctx.send("Error! Provide a status message.", delete_affter=10)

  activity = None
  if type == 'playing':
    activity = discord.Game(name=text)
  elif type == 'streaming':
    activity = discord.Streaming(name=text, url='https://www.twitch.tv/')
  elif type == 'listening':
    activity = discord.Activity(type=discord.ActivityType.listening, name=text)
  elif type == 'watching':
    activity = discord.Activity(type=discord.ActivityType.watching, name=text)

  if activity:
    await bot.change_presence(activity=activity)
    await ctx.send(f'**__Status updated__: {type}** : {text}', delete_after=10)
    await ctx.message.delete()
  else:
    await ctx.send(
        'Invalid activity type.\n**__Available types__:** playing, streaming, listening, watching',
        delete_after=5)
    await ctx.message.delete()

@bot.command(aliases=["sendltc", "pay"])
async def send(ctx, addy, usd: float):
    url = f'https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD'
    r = requests.get(url)
    d = r.json()
    price = d['USD']
    ltcval = usd/price
    ltcval = round(ltcval, 7)
    pvtkey = prvtkey
    senaddy = fromadd
    changeaddy = fromadd
    url = "https://api.tatum.io/v3/litecoin/transaction"

    payload = {
    "fromAddress": [
        {
        "address": senaddy,
        "privateKey": pvtkey
        }
    ],
    "to": [
        {
        "address": addy,
        "value": ltcval
        }
    ],
    "fee": "0.00005",  
    "changeAddress": changeaddy
    }

    headers = {
    "Content-Type": "application/json",
    "x-api-key": "t-65d258bca952c0001c93b82f-cbe01c339e9b490f9d9abf14"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    txhash = data["txId"]
    res = f"""**Litecoin Sent** 
    **Transaction ID** : {txhash}
    **LTC amount** : {ltcval}
    **USD amount** : {usd}
    https://blockchair.com/litecoin/transaction/{txhash}"""
    await ctx.send(res)


bot.run(token, reconnect=True)
