import discord
from discord.ext import commands
import requests
import random
import json
import os
import math

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='c!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command(name='start')
async def start(ctx):
    # Welcome embed
    welcome_embed = discord.Embed(title="Welcome to the Pokemon RPG!", description="To begin, please enter your name:", color=discord.Color.blue())
    await ctx.send(embed=welcome_embed)

    def check_name(msg):
        return msg.author == ctx.author

    user_name_msg = await bot.wait_for('message', check=check_name)
    user_name = user_name_msg.content

    # Display ToS with Imgur image
    tos_embed = discord.Embed(title="Terms of Service", description="By playing this game, you agree to the following terms:", color=discord.Color.purple())
    tos_embed.set_thumbnail(url="https://i.imgur.com/y2xiwc6.png")  # Replace with your Imgur image URL
    tos_content = (
        "1. Agreement: By continuing, you agree to abide by the rules and guidelines set forth in this game.\n"
        "2. Roleplay: You are expected to immerse yourself in the roleplay world of Pokemon.\n"
        "3. Respect: Treat others with respect and kindness. Harassment and hate speech will not be tolerated.\n"
        "4. Fair Play: Play fairly and avoid cheating or exploiting game mechanics.\n"
        "5. Privacy: Do not share personal information or engage in any activities that compromise your privacy.\n"
        "6. Enjoyment: Most importantly, have fun and enjoy your Pokemon adventure!"
    )
    tos_embed.add_field(name="Terms and Conditions", value=tos_content, inline=False)
    await ctx.send(embed=tos_embed)

    # Display starter choices
    starter_names = ['Bulbasaur', 'Charmander', 'Squirtle']
    starter_choice_embed = discord.Embed(description="Please choose your starter by typing the number of your choice (1, 2, or 3):", color=discord.Color.blue())
    starter_choices = "\n".join([f"{idx}. {name}" for idx, name in enumerate(starter_names, start=1)])
    starter_choice_embed.add_field(name="Starter Choices", value=starter_choices)
    await ctx.send(embed=starter_choice_embed)

    def check_choice(msg):
        return msg.author == ctx.author and msg.content in ['1', '2', '3']

    user_choice_msg = await bot.wait_for('message', check=check_choice)
    user_choice = int(user_choice_msg.content) - 1  # Convert to 0-based index

    chosen_starter = starter_names[user_choice]
    user_id = str(ctx.author.id)  # Add this line to get the user_id

    user_data = {
        'name': user_name,
        'level': 1,
        'experience': 0,
        'caught_pokemon': [],
        'starter': chosen_starter,
    }

    save_user_data(user_id, user_data)

    # Display combined embed
    combined_embed = discord.Embed(title=f"Welcome to the world of Pokemon, {user_name}!",
                                   description=f"You've chosen {chosen_starter} as your starter!\nBegin your adventure and catch 'em all!",
                                   color=discord.Color.gold())
    combined_embed.set_thumbnail(url="https://i.imgur.com/y2xiwc6.png")  # Replace with your Imgur image URL
    combined_embed.set_footer(text="Enjoy the game!")
    await ctx.send(embed=combined_embed)

@bot.command(name='catch')
async def catch(ctx):

  # Get random id
  random_id = random.randint(1,1015)

  api_url = f"https://pokeapi.co/api/v2/pokemon/{random_id}"
  
  response = requests.get(api_url)
  if response.status_code != 200:
      await ctx.send("Error finding pokemon data.")
      return

  pokemon_data = response.json()  

  # Get user data
  user_id = str(ctx.author.id)
  user_data = load_user_data(user_id)

  if user_data is None:
      await ctx.send("You need to start first using c!start.")
      return

  # Add to caught list
  user_data['caught_pokemon'].append(pokemon_data['name'])

  # Gain exp
  exp_gained = random.randint(10, 100)
  user_data['experience'] += exp_gained

  # Check for level up
  if user_data['experience'] >= 100 * user_data['level']:
      user_data['level'] += 1
      lvl_up_msg = f"You leveled up to {user_data['level']}!"
  else:
      lvl_up_msg = ""

  # Build embed  
  embed = discord.Embed(
      title=f"You caught a {pokemon_data['name']}!",
      description=f"{lvl_up_msg}\nExp gained: {exp_gained}"
  )

  embed.set_thumbnail(url=pokemon_data['sprites']['other']['official-artwork']['front_default'])
  
  embed.add_field(name="Height", value=pokemon_data['height'])
  embed.add_field(name="Weight", value=pokemon_data['weight'])

  # Save user data
  save_user_data(user_id, user_data)

  await ctx.send(embed=embed)

@bot.command(name='profile')
async def profile(ctx):

  # Get user data
  user_id = str(ctx.author.id)
  user_data = load_user_data(user_id)

  if user_data is None:
    await ctx.send("You must start first using c!start")
    return

  # Paginate caught Pokemon
  pokemon_per_page = 10
  total_pages = math.ceil(len(user_data['caught_pokemon']) / pokemon_per_page)

  for i in range(total_pages):
    start_idx = i * pokemon_per_page
    end_idx = start_idx + pokemon_per_page

    pokemon = user_data['caught_pokemon'][start_idx:end_idx]

    embed = discord.Embed(title=f"Caught Pokemon - Page {i+1}/{total_pages}")
    embed.add_field(name="Pokemon", value="\n".join(pokemon))
    
    await ctx.send(embed=embed)

  # Profile embed
  embed = discord.Embed(title=f"{ctx.author.name}'s Profile")

  # Add favorite 
  favorite = user_data.get('favorite_pokemon')
  if favorite: 
    embed.add_field(name="Favorite Pokemon", value=favorite)

  await ctx.send(embed=embed)


@bot.command(name='favorite')
async def set_favorite(ctx, pokemon):
  
  # Set in user data
  user_id = str(ctx.author.id)
  user_data = load_user_data(user_id)

  user_data['favorite_pokemon'] = pokemon

  await ctx.send(f"Your favorite Pokemon has been set to {pokemon}!")

def load_user_data(user_id):
    try:
        with open(f'{user_id}.json', 'r') as f:
            user_data = json.load(f)
            return user_data
    except FileNotFoundError:
        return None

def save_user_data(user_id, user_data):
    with open(f'{user_id}.json', 'w') as f:
        json.dump(user_data, f, indent=4)

def get_pokemon_data(pokemon_id):
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}/")
    data = response.json()

    name = data['name']
    types = [t['type']['name'] for t in data['types']]
    sprites = data['sprites']
    stats = data['stats']

    return {'id': pokemon_id, 'name': name.capitalize(), 'types': types, 'sprites': sprites, 'stats': stats}

@bot.command(name='evolve')
async def evolve(ctx, pokemon: str):
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pokemon.lower()}")
    if response.status_code != 200:
        await ctx.send(f"Error: {pokemon} not found.")
        return

    species_data = response.json()
    evolution_chain_url = species_data['evolution_chain']['url']

    evolution_chain_response = requests.get(evolution_chain_url)
    if evolution_chain_response.status_code != 200:
        await ctx.send(f"Error retrieving evolution chain for {pokemon}.")
        return

    evolution_chain_data = evolution_chain_response.json()
    current_species = evolution_chain_data['chain']['species']['name']
    evolutions = []

    while 'evolves_to' in evolution_chain_data['chain']:
        evolution = evolution_chain_data['chain']['evolves_to'][0]['species']['name']
        evolutions.append(evolution)
        evolution_chain_data = evolution_chain_data['chain']['evolves_to'][0]

    if not evolutions:
        await ctx.send(f"{pokemon} does not have any evolutions.")
    else:
        evolutions_str = ", ".join(evolutions)
        await ctx.send(f"{pokemon} evolves into: {evolutions_str}")



# Dex command to view Pokemon info
@bot.command(name='dex')
async def pokedex(ctx, pokemon):

  # Get Pokemon data
  pokemon_data = get_pokemon_data(pokemon) 
  
  if not pokemon_data:
    await ctx.send("Pokemon not found!")
    return
  
  # Build embed    
  embed = discord.Embed(title=pokemon_data['name'], color=discord.Color.blue())
  embed.set_thumbnail(url=pokemon_data['sprite'])
  embed.add_field(name="Number", value=pokemon_data['id'])
  embed.add_field(name="Type", value=", ".join(pokemon_data['types']))

  await ctx.send(embed=embed)
    
# Run the bot
bot.run(os.getenv("TOKEN"))
