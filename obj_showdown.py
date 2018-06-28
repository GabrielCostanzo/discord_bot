import discord
import sys
import requests
import operator
import asyncio

import threading
import pickle
import os

import datetime 

from datetime import timedelta
import time
import random

#from hashlib import blake2b

import pickle

start_switch = False
end_switch = False
#discord bot token here
TOKEN = 'xxxxxxx'


#fortnite tracker api key here
key = {'TRN-Api-Key':"xxxxxx"}

master_key = b'pseudorandomly generated server secret key'

auth_size = 16

client = discord.Client()
rank_data_dict = {}

def sign(user, in_key):
	"""
	h = blake2b(digest_size = auth_size, key = in_key)
	h.update(user)
	return h.hexdigest()
	"""
	return random.randint(0, 99999999)

def encrypt_key(access_key, secret_key):
	encrypted = (sign(access_key, secret_key))

	return encrypted

class player():
	def __init__(self, username):
		self.username = username
		self.start_kills = None

	def get_player_info(self):
		URL = "https://api.fortnitetracker.com/v1/profile/pc/"+self.username

		try:
			r = requests.get(url = URL,headers=key)
			data = r.json()
			kd = data['lifeTimeStats'][11]['value']
			wins = data['lifeTimeStats'][8]['value']
			matchesPlayed = data['lifeTimeStats'][7]['value']
			kills = data['lifeTimeStats'][10]['value']
			winrate = int(matchesPlayed)/int(wins)
			winrat = str(int(winrate))

			return kills
		except:
			return False
		#overall data above

class battle():
	instances = []
	def __init__(self, duration):
		self.id = None
		self.player_list = []

		self.creation_time = datetime.datetime.now()
		self.duration = duration*3600
		self.delta_seconds = 900
		self.start_time = self.creation_time + timedelta(seconds=self.delta_seconds)
		self.end_time = None

		def set_id(self):
			self.id = str(sign(str(self.creation_time).encode('UTF-8'), master_key))
		set_id(self)
		battle.instances.append(self)

	def add_player(self, username):
		new_player = player(username)
		self.player_list.append(new_player)

		return new_player

	def start_battle(self):
		global start_switch 
		#print("a battle has been started")
		self.start_time = datetime.datetime.now()
		self.end_time = self.start_time + timedelta(seconds=self.duration)
		for i in self.player_list:
			i.start_kills = i.get_player_info()
		start_switch = True

		threading.Timer(self.duration, self.end_battle).start()


	def end_battle(self):
		global end_switch
		global rank_data_dict
		#print("battle ended")
		#print("battle list\n\n", battle.instances)
		#print(self.player_list)
		for i in self.player_list:
			end_kills = i.get_player_info()
			rank_data_dict[i.username] = int(end_kills) - int(i.start_kills)
		#print ("rank_data_dict", rank_data_dict)
		battle.instances.remove(self)
		end_switch = True



@client.event
async def on_message(message):
	global start_switch
	global end_switch
	global rank_data_dict
	message_word_list = message.content.split()

	if message.author == client.user:
		return

	if message_word_list[0] == '$help':
		msg = '''Create a Fortnite deathmatch!\nWho can get the most kills before the timer runs out?\n\nCreate a deathmatch:\n$start [hours] ```$start 2```\nJoin a deathmatch:\n$join [deathmatch_id] [fortnite_name]```$join aafecbe342 Ninja```'''
		await client.send_message(message.channel,msg)

	if message_word_list[0] == '$kill':
		msg = "bot used dodge. very effective!"
		await client.send_message(message.channel, msg)
		#sys.exit()


	if message_word_list[0] == '$start':
		try:
			new_battle = battle(float(message_word_list[1]))
			threading.Timer(new_battle.delta_seconds, new_battle.start_battle).start()

		except IndexError:
			new_battle = battle(1)
			threading.Timer(new_battle.delta_seconds, new_battle.start_battle).start()

		#correct for timezone
		hour = str(int(new_battle.start_time.hour-5))
		minute = str(new_battle.start_time.minute)
		if int(hour) < 0:
			hour = str(int(hour)+12)
			stamp = "PM CST"
		elif int(hour) > 12:
			stamp = "PM CST"
		else:
			stamp = "AM CST"
		if hour == '0':
			hour = '12'
		if len(minute) == 1:
			minute = '0'+ minute
		if int(hour) > 12:
			hour = str(int(hour)-12)

		#print(hour, new_battle.start_time, stamp)

		msg = ("A new deathmatch has been initiated:\nto join, paste:\n ```$join %s NAME``` \nThe match will begin at: %s:%s %s"%(new_battle.id, hour, minute, stamp))
		await client.send_message(message.channel,msg)

		while start_switch == False:
			await asyncio.sleep(1)
		start_switch = False
		msg = "deathmatch ```%s``` has started!"%new_battle.id
		await client.send_message(message.channel,msg)

		while end_switch == False:
			await asyncio.sleep(1)
		end_switch = False

		msg = "Results are in for deathmatch ```%s```\n"%new_battle.id
		await client.send_message(message.channel, msg)
		sorted_rank_data = sorted(rank_data_dict.items(), key = operator.itemgetter(1))
		count = 1 
		#print("sorted_rank_data:", sorted_rank_data)
		for i in sorted_rank_data[::-1]:
			msg = "%s.\t%s:\t%s"%(count, i[0], i[1]) 
			await client.send_message(message.channel, msg)
			count += 1
		rank_data_dict = {}

	if message_word_list[0] == '$join':
		#print(message_word_list[1])
		name = ""
		for i in (message_word_list[2:]):
			name += i
			name += " "
			print(name)

		for i in range(len(battle.instances)):
			battle_id = (battle.instances[i].id)
			battle_obj = battle.instances[i]
			if battle_id == str(message_word_list[1]):
				added_player = player(name)

				if added_player.get_player_info() == False:
					msg = "%s is not a recognized player please try again!"%name
					await client.send_message(message.channel,msg) 
				else:
					dup = False
					for j in battle_obj.player_list:
						if j.username == name:
							msg = "%s has already been entered!"%name
							await client.send_message(message.channel,msg)
							dup = True

					if dup == False:
						battle_obj.player_list.append(added_player)
						msg = "%s joined the ```%s``` deathmatch!\nThere are now %s players"%(name, battle_id, len(battle_obj.player_list))
						#print("\n", battle_obj.player_list, "\n")
						await client.send_message(message.channel,msg)
					
@client.event
async def on_ready():
	print('Logged in as')
	print(client.user.name,'\n',client.user.id)
	print('_________')

client.run(TOKEN)
