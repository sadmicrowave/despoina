#!/usr/local/bin/python3

# Note: in most game programming the x-y coordinate plane is different 
# from the one you learned in algebra. In the game world, (0,0) is in 
# the top left corner, x increases to the right, and y increases to the bottom.

import random, inspect, math, textwrap, copy
from modules.bgcolors import BgColors
from modules import actions
from modules import items
from modules import armor
from modules import weapons
#from modules import world
from modules import enemies
from modules.helpers import health


# The MapTile class is going to provide a template for all of the tiles in our world, 
# which means we need to define the methods that all tiles will need.
class MapTile:
	# MapTile is actually a specific flavor of a base class.  We call it an abstract 
	# base class because we don’t want to create any instances of it.
	item = None
	def __init__(self, name, description, visited_description=None, item=[], interaction_item=[], isBlocked=False, floor=1):
		self.name = name
		self.x = None
		self.y = None
		self.description 			= description
		self.visited_description 	= (visited_description or "This appears to be an unremarkable area.") + "  You've been here before."
		self.objects 				= item
		self.isBlocked 				= isBlocked
		self.interaction_item 		= interaction_item
		self.visited 				= False
		self.floor 					= int(floor)
       
	# We will never create a MapTile directly, instead we will create subclasses. 
	# The code raise NotImplementedError() will warn us if we accidentally create a MapTile directly.
	#def intro_text(self):
	#	return self.description
	
	#def intro_text(self):
	#	return self.description
	
	def intro_text(self, player=None):
		message = None
		#for item in self.objects:
		#	if isinstance(item, items.Movable):
		#		message = self.description if not item.unblocked else "You see a moved {} in the room.  You've been here before.".format(item.name)
				
		if not message:
			message = self.description if not self.visited else self.visited_description
		return message	
 
	def modify_player(self, player):
		pass
	
	def modify_player(self, player):
		pass
	
	def add_item(self, item):
		self.objects.append( item )
	
	def remove_item(self, item):
		self.objects.remove( item )
	
	def get_items(self):
		return self.objects
		
	def reindex_items(self):
		i = 0		
		for index, item in enumerate(self.objects):	
			i += 1
			self.objects[index].index = i
	
	def is_visited(self):
		return self.visited == True
	
	# These methods provide some default behavior for a tile. The default actions that a player should have are: 
	# move to any adjacent tile and view inventory. The method adjacent_moves determines which moves are possible in the map. 
	# For each available action, we append an instance of one of our wrapper classes to the list. Since we used the wrapper 
	# classes, we will later have easy access to the names and hotkeys of the actions.
	def adjacent_moves(self, player=None):
		"""Returns all move actions for adjacent tiles."""
			
		moves = []
		if not self.isBlocked :		
			if player.world.__dict__.get('(%s, %s)' % (self.x + 1, self.y) ):
				moves.append(actions.MoveEast())
			if player.world.__dict__.get('(%s, %s)' % (self.x - 1, self.y)):
				moves.append(actions.MoveWest())
			if player.world.__dict__.get('(%s, %s)' % (self.x, self.y - 1)):
				moves.append(actions.MoveNorth())
			if player.world.__dict__.get('(%s, %s)' % (self.x, self.y + 1)):
				moves.append(actions.MoveSouth())
		
		else :
			# get the moves to go back to the previous location
			if self.x < player.prev_location_x :
				moves.append(actions.MoveEast())
			if self.x > player.prev_location_x :
				moves.append(actions.MoveWest())
			if self.y < player.prev_location_y :
				moves.append(actions.MoveSouth())
			if self.y > player.prev_location_y :
				moves.append(actions.MoveNorth())
			
		return moves

	def available_actions(self, player=None):
		"""Returns all of the available actions in this room."""
		buf = []
		
		moves = self.adjacent_moves(player)
		
		if self.objects:
			for item in self.objects:
				if isinstance(self, EnemyRoom) and self.enemy.objects:
					buf.append( actions.Loot(enemy=self.enemy) )
				elif isinstance(self, RepairVendorRoom):
					buf.append( actions.Repair(vendor=self.vendor) )
				#print( isinstance(item, items.Readable), item )
				elif isinstance(item, items.Container) and item.unblocked and not item.opened:
					buf.append( actions.Open() )
				elif not isinstance(item, items.Container) and not isinstance(item, items.Readable) and not isinstance(item, items.Movable) and not isinstance(item, enemies.Enemy):
					buf.append( actions.PickUp() )
				elif isinstance(item, items.Readable) : #and not item.is_read():
					buf.append( actions.Read() )
				elif ( isinstance(item, items.Movable) and not item.unblocked ) or ( isinstance(item, items.Container) and not item.unblocked and not item.opened ):
					buf.append( actions.UseAction() )				
				
		
		# append a unique list of the available action objects (from buf) to moves.  This converts the list to
		# a dict, then removes duplicates, then converts the dict back to a list in order to append
		moves += list({type(k): k for k in buf}.values())
		
		moves += [actions.Inventory()
				
				,actions.CheckHp()
				,actions.CheckStats()
				,actions.Drop()
				,actions.Equip()
				,actions.Journal()
				,actions.Map()
				,actions.Quit()
				,actions.ReadHidden()
				,actions.Search()
				,actions.Skills()
				,actions.Save()
				,actions.Use()
				,actions.UnEquip()				
				]
				
		if self.name == 'LeaveCaveRoom' and not self.isBlocked:
			moves += [actions.Exit()]
		
		moves += [actions.Help()]
		
		return moves



#################################################################################################################################
# DEFINE TILES OF THE WORLD

class LeaveCaveRoom(MapTile):
	def __init__(self, name, description, visited_description, item=[], interaction_item=None, isBlocked=False, floor=1):
		super().__init__(name, description, visited_description, item, interaction_item, isBlocked, floor)
	
	def modify_player(self, player):
		player.victory = True

	
#class LootRoom(MapTile):
#	def __init__(self, name, description, visited_description, item=[], interaction_item=None, isBlocked=False, floor=None):
#		super().__init__(name, description, visited_description, item, interaction_item, isBlocked, floor)
#
#	def intro_text(self):
#		return self.description if self.objects and not self.visited else self.visited_description
#	
#	def modify_player(self, player):
#		pass


# A tile to encounter an new enemy
class EnemyRoom(MapTile):
	def __init__(self, name, description, visited_description=None, enemy=[], interaction_item=[], isBlocked=False, floor=1):
	#def __init__(self, x, y, enemy, interaction_item=None, isBlocked=False, floor=1):
		self.enemy = enemy[0]
		#super().__init__(x, y)
		super().__init__(name, description, visited_description, enemy, interaction_item, isBlocked, floor)
	
	def modify_player(self, player):
		# We didn’t want enemies to respawn. So if the player already visited 
		# this room and killed the enemy, they should not engage battle again.
		# So we check if enemy is still alive...
		#if self.enemy.is_alive():
		if health.Health.is_alive(self.enemy):
			# provide a likelihood that the enemy will strike you, based on the evade skill
			if random.random() > (player.skills['evade']['value']/100): 
			
				# get full armor level by adding blocking power of all armor in inventory that is equipped
				armor_level = sum( [x.block for x in player.inventory if isinstance(x, armor.Armor) and x.is_equipped()] )
				# get the list of all inventory armor items that are equipped, in order to calculate the armor/block level
				equipped = [x for x in player.inventory if isinstance(x, armor.Armor) and x.is_equipped()]

				#damage = (self.enemy.damage-armor_level) #if self.enemy.damage > armor_level else 0
				damage = self.enemy.damage
								
				# set the damage that the enemy can do, based on blocking capability against enemy damage
				#damage_inflicted = ( damage * (1-(player.skills['block']['value']/100)) ) if armor_level else damage #/ len(equipped)
				#damage = damage_inflicted
				total_degrade = 0
				broken = []
				# split the damage inflicted across all equipped armor to equally degrade any armor that is equipped, and decrease potential damage each time, for a potential final damage amount on the player hp
				for i in equipped :
					# enemy_damage * [inverse of blocking skill points] / [number of equipped armor items]
					#armor_damage = damage*(1-(player.skills['block']['value']/100)) / len(equipped)
					
					#i.hp = max(round( i.hp - (damage_inflicted/len(equipped)),2) if i.level <= self.enemy.level else i.hp,0)
					degrade = ( damage * (1-(player.skills['block']['value']/100)) ) / len(equipped) if armor_level else 0
					i.hp = max(round( i.hp - degrade, 2) if i.level <= self.enemy.level else i.hp,0)
					if i.hp <= 0 :
						i.equip = False
						broken.append( i )
						#print("{}The {} has broken! Equip different armor!{}".format(BgColors.FAIL, i.name, BgColors.ENDC))
					
					# decrease the remaining amount of damage by the amount of defense the item has
					#damage = max(damage - (armor_level/len(equipped)),0)
					damage = max(damage - i.block,0)
					total_degrade += degrade
				
				#armor_quote = ". Your armor blocks {}!".format( min(damage_inflicted,armor_level) ) if armor_level else '!'
				#armor_quote = ". Your armor blocks {}!".format( min(round(total_degrade,2), armor_level) ) if armor_level else '!'
				#print("{}Enemy attacks with {} damage{}{}".format(BgColors.FAIL, round(damage_inflicted,2), armor_quote, BgColors.ENDC))
				#print("{}Enemy attacks with {} damage{}{}".format(BgColors.FAIL, round(damage_inflicted,2), armor_quote, BgColors.ENDC))
				print("")
				print("{}{} attacked:{}".format(BgColors.NORMAL, self.enemy.name, BgColors.ENDC))
				if armor_level :
					print("{}Your armor blocks {} DMG!{}".format(BgColors.WARNING, self.enemy.damage-damage, BgColors.ENDC))
				print("{}┌{}┐".format(BgColors.FAIL,"─"*50))
				print("|", "{:<24}|".format('Attack'), "{:<23}|".format( "%s/%s DMG" % (damage, self.enemy.damage) ))
				print("|", "{:<24}|".format('Enemy HP'), "{:<23}|".format("%s/%s" % (self.enemy.hp, self.enemy.orig_hp) ))
				print("{}└{}┘".format(BgColors.FAIL, "─"*50))
				#print("{}Your armor blocks {}!{}".format(BgColors.WARNING, min(round(total_degrade,2), armor_level), BgColors.ENDC) if armor_level else "")
				
				if broken :
					for item in broken: 
						print("{}The {} has broken! Equip different armor!{}".format(BgColors.FAIL, item.name, BgColors.ENDC))
				
				# adjust player health based on remaining damage after armor blocks
				player.hp = max(int(player.hp - damage),0)
			
			else:
				print("{}\nEnemy missed!{}".format(BgColors.FAIL, BgColors.ENDC))
			
			#print("{}Enemy HP: {}{}".format(BgColors.FAIL, self.enemy.hp, BgColors.ENDC))
			#print("{}Your HP: {}{}".format(BgColors.OKGREEN, player.hp, BgColors.ENDC))
	
	
	# Add the attack and flee action options to any enemy room
	def available_actions(self, player=None):
		# If the enemy is still alive then the player’s only options are attack or flee. 
		# If the enemy is dead, then this room works like all other rooms.
		
		a = None
		# if last location x is greater than current location x, then we must have moved west to get here, move east would be reverse
		if self.x < player.prev_location_x :
			a = actions.MoveEast()
		# if last location x is less than current location x, then we must hav emoved east to get here, move west would be reverse
		if self.x > player.prev_location_x :
			a = actions.MoveWest()
		# if last location y is greater than current location y, then we must of have moved north to get here, move south would be reverse
		if self.y < player.prev_location_y :
			a = actions.MoveSouth()
		# if last location y is less than current location y, then we must have moved south to get here, move north would be reverse
		if self.y > player.prev_location_y :
			a = actions.MoveNorth()		
		
		if health.Health.is_alive(self.enemy):
			return [ a
				#,actions.Flee(tile=self)
				,actions.Attack(enemy=self.enemy)
				,actions.Equip()
				,actions.UnEquip()
				,actions.Inventory()
				,actions.Help()
				,actions.Use()
				,actions.CheckHp()
				,actions.CheckStats()
				,actions.Skills()
				,actions.Quit()
				]
		#elif not self.enemy.is_alive() and self.enemy.loot_type and not self.enemy.been_looted():
		elif not health.Health.is_alive(self.enemy) and self.enemy.loot_type and not self.enemy.been_looted():
			# create some objects on the enemy to loot if they don't already exist
			if not self.enemy.objects:
				#r = random.random()
				#s = player.skills['loot']['value']/100
				if random.random() <= (player.skills['loot']['value']/100): 	
				#if r <= s:
					loot = []
					# get a full list of all the lootable objects from the items master list
					for k, v in player.world._objects.items():
						# only add the item to the loot container if the item is of class type lootable, matches the same lootable type as the enemy has in loot_type, and is the same level as the enemy
						if issubclass(v.__class__, items.Lootable) and self.enemy.match_loot_type(v) and v.level == self.enemy.level:
							loot.append( v )
					
					# randomly shuffle the loot list
					random.shuffle(loot)
					# only allow the number of loot items to equal the level of the enemy
					loot = loot[0:self.enemy.level]
					# ensure the loot list is not empty
					if loot :
						# calculate number of objects to be looted, based on threshold defined from player looting skill
						#ran = min(math.floor(s/r), math.floor(100*(s/5)))
						# iterate for as many times as "ran" variable says there should be items lootable on the enemy
						#for x in range( ran ):
						for item in loot:
							# randomly select one of the lootable items inside the master loot container
							#loot_index = random.randint(1, len(loot))-1
						
							try:
								#obj = loot[ loot_index ]
								#item_name = obj.name.replace(' ','')
								
															
								#if issubclass(obj.__class__, weapons.Weapon):
								#	# define an __init__ constructor method to be used when dynamically creating the object class
								#	def __constructor__(self, n, cl, d, c, da, h, l):
								#		# initialize super of class type
								#		super(self.__class__, self).__init__(name=n, classtype=cl, description=d, cost=c, damage=da, hp=h, level=l)
								#	
								#	# create the object class dynamically, utilizing __constructor__ for __init__ method
								#	item = type(obj.name, (eval("{}.{}".format("weapons",obj.classtype.replace(' ',''))),), {'__init__':__constructor__})
								#	# add new object to the global _objects object to be used throughout the world
								#	item = item(obj.name, obj.classtype, obj.description, obj.cost, obj.damage, obj.orig_hp, obj.level)
					
								#if issubclass(obj.__class__, armor.Armor):
								#	def __constructor__(self, n, cl, d, c, b, h, l):
								#		# initialize super of class type
								#		super(self.__class__, self).__init__(name=n, classtype=cl, description=d, cost=c, block=b, hp=h, level=l)
								#
								#	# create the object class dynamically, utilizing __constructor__ for __init__ method
								#	item = type(obj.name, (eval("{}.{}".format("armor",obj.classtype.replace(' ',''))),), {'__init__':__constructor__})
								#	# add new object to the global _objects object to be used throughout the world
								#	item = item(obj.name, obj.classtype, obj.description, obj.cost, obj.block, obj.hp, obj.level)
								
								#if issubclass(obj.__class__,items.Money):
								#	def __constructor__(self, n, cl, d, a):
								#		# initialize super of class type
								#		super(self.__class__, self).__init__(name=n, classtype=cl, description=d, amt=a)
								#	
								#	# create the object class dynamically, utilizing __constructor__ for __init__ method
								#	item = type(obj.name, (eval("{}.{}".format("money",obj.classtype.replace(' ',''))),), {'__init__':__constructor__})
								#	# add new object to the global _objects object to be used throughout the world
								#	amt = math.floor(random.randint(math.floor(100*(s/5)), math.floor(100*s)))
								#	
								#	item = item(obj.name, obj.classtype, obj.description, amt)
								
								# remove the item from master lootable index so we can't select it again
								#del loot[ loot_index ]
							
								#amt = ""
								#
								#	amt = math.floor(random.randint(math.floor(100*(s/5)), math.floor(100*s)))
								
								# place the item/object onto the enemy
								#self.enemy.objects.append( item )
								self.enemy.objects.append( copy.deepcopy(item) )  
								
							except IndexError:
								pass
				
		action_list = super().available_actions(player)
		
		#if self.enemy.objects:
		#	action_list += [actions.Loot(enemy=self.enemy)]
            
		return action_list
		
		
	def intro_text(self, player=None):
		print( textwrap.fill( self.description if not self.visited else self.visited_description, 70) )
	
		#if self.enemy.is_alive():		
		if health.Health.is_alive(self.enemy):
			print("\n{}┌{}┐".format(BgColors.FAIL, "─"*50))
			print("|", "{:<25}|".format('Name'), "{:<4}|".format("HP"), "{:<16}|".format("Damage"))
			#print("|", "{:<3}|".format('#'), "{:<20}|".format('Name'), "{:<7}|".format('Value'), "{:<5}|".format("HP"), "{:<5}|".format("DEF"), "{:<5}|".format("DMG"), "{:<53}|".format("Description")) #{:<20}

			print("| {} |".format("─"*48))
			print("|", "{:<25}|".format(self.enemy.name), "{:<4}|".format(self.enemy.hp), "{:<16}|".format(self.enemy.damage))
			
			print("└{}┘".format("─"*50))
			print("{}Check your current stats with the [cs] command.".format(BgColors.NORMAL))
			
		return None			
			

class MerchantRoom(MapTile):
	def __init__(self, x, y, merchant, interaction_item=None, isBlocked=False, floor=None):
		# items is a dict of items to sell and buy
		self.merchant = merchant
		
		#self.merchant = eval("merchants.Merchant{}()".format(merchant))
		super().__init__(x, y)

	# Add the buy, sell, and list action options to any enemy room
	def available_actions(self, player=None):        
		available_actions = [actions.Buy(merchant=self.merchant)
							,actions.Sell(merchant=self.merchant)
							,actions.List(merchant=self.merchant)
							]
		available_actions += super().available_actions(player)

		return available_actions

	def modify_player(self, player):
		pass

	def get_items(self):
		return self.merchant

	def intro_text(self, player=None):
		return self.description if not self.visited else self.visited_description
		


class RepairVendorRoom(MapTile):
	#def __init__(self, x, y, vendor, interaction_item=None, isBlocked=False, floor=None):
	def __init__(self, name, description, visited_description=None, vendor=[], interaction_item=[], isBlocked=False, floor=1):
		self.vendor = vendor
		super().__init__(name, description, visited_description, vendor, interaction_item, isBlocked, floor)
		#super().__init__(x, y)

	# Add the buy, sell, and list action options to any enemy room
	def available_actions(self, player=None):        
		available_actions = super().available_actions(player)
		#available_actions += [actions.Repair(vendor=self.vendor)]
		return available_actions

	def modify_player(self, player):
		pass

	def intro_text(self, player=None):
		print( textwrap.fill( self.description if not self.visited else self.visited_description ) )
		
		# get a list of all the items within your inventory that might need repair
		repairable = [x for x in player.inventory if ( isinstance(x, armor.Armor) or isinstance(x, weapons.Weapon) and x.hp != x.orig_hp )]

		if list(filter(None.__ne__, repairable)):
			
			print("\nRepairable Items in your inventory:")
			print("{}┌{}┐".format(BgColors.NORMAL,"─"*106))
			print("|", "{:<3}|".format('#'), "{:<20}|".format('Name'), "{:<7}|".format("HP"), "{:<7}|".format('Cost'), "{:<5}|".format("DMG"), "{:<53}|".format("Description")) #{:<20}
				
			if len([x for x in repairable if isinstance(x, weapons.Weapon)]) > 0:
				print("{}| {} |{}".format(BgColors.NORMAL, "─"*104, BgColors.ENDC))
				for index, item in enumerate(repairable):
					if isinstance(item, weapons.Weapon) :
						cost = self.vendor[0].repair_cost(item)
						print("{}| {:<3}|".format(BgColors.NORMAL, item.index), "{:<20}|".format(item.name if len(item.name) <= 20 else item.name[0:17]+'...'), "{:<7}|".format( "%s/%s" % (item.hp, item.orig_hp) ), "{:<7}|".format(cost), "{:<5}|".format(item.damage), "{:<53}{}|".format(item.description if len(item.description) <= 53 else item.description[0:50]+'...', BgColors.ENDC)) #{:<20}
						
			if len([x for x in repairable if isinstance(x, armor.Armor)]) > 0:
				print("{}| {} |{}".format(BgColors.NORMAL, "─"*104, BgColors.ENDC))
				for index, item in enumerate(repairable):
					if isinstance(item, armor.Armor) :
						cost = self.vendor[0].repair_cost(item)
						print("{}| {:<3}|".format(BgColors.NORMAL, item.index), "{:<20}|".format(item.name if len(item.name) <= 20 else item.name[0:17]+'...'), "{:<7}|".format( "%s/%s" % (item.hp, item.orig_hp) ), "{:<7}|".format(cost), "{:<5}|".format(''), "{:<53}{}|".format(item.description if len(item.description) <= 53 else item.description[0:50]+'...', BgColors.ENDC)) #{:<20}
												
			print("{}└{}┘".format(BgColors.NORMAL, "─"*106))
		
		else :
			print("{}You have nothing to repair.{}".format(BgColors.NORMAL, BgColors.ENDC))
		
		return None
		


        
        
        
        
        
        
        
