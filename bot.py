# libraries :) :D
from penguin_game import *
import math
import itertools

# global variable for saving the game's given parameters;
turnfo = None
#determins the density of the icebergs in the map;
density = 0
# the number of turns we look into the  future ;
turn_skope = 0


class Game_Info:
    """
    This class updates all the constant parameters for each turn;

    my_id   - our id[int];
    en_id   - enemy id[int];

    all_ice - list of all icebergs(including bonus)[list];
    my_ice  - list of all our icebergs[list];
    en_ice  - list of all enemy icebergs[list];
    nu_ice  - list of all neutral icebergs[list];

    bu_ice  - the bouns iceberg;
    
    penguins_to_dest    - dictionary of the penguins groups aheding to a iceberg[dict];
                        dict format: {ice1:[group1,group3],ice2:[],ice3:[group2],...}
    
    bridge_multi        - the speed multiplayer the bridge provides;
    bridge_max_duration - the maximum turns the bridge will last;
    bridge_cost         - the cost of building a bridge;

    turn_skope          - the number of turns we look into the  future  ;
    density             - the density of the map;
    
    """

    def __init__(self, game):
        # get IDs
        self.en_id = game.get_enemy_icebergs()[0].owner.id
        self.my_id = 0 if self.en_id == 1 else 1

        # get the lists of the icebergs;
        self.my_ice = None
        self.en_ice = game.get_enemy_icebergs()
        self.nu_ice = game.get_neutral_icebergs()
        self.bu_ice = None

        # bonus information
        try:
            self.bu_ice = game.get_bonus_iceberg()
            self.max_turns_to_bonus = self.bu_ice.max_turns_to_bonus
            self.bonus = game.bonus_iceberg_penguin_bonus
        except AttributeError:  # the game doesn't have any bonus icebergs;
            self.bu_ice = None
            self.bonus = None
            self.max_turns_to_bonus = None
            
        # bridge information;
        try:
            self.bridge_multi = game.iceberg_bridge_speed_multiplier
            self.bridge_max_duration = game.iceberg_max_bridge_duration
            self.bridge_cost = game.iceberg_bridge_cost
        except AttributeError:
            self.bridge_multi = None
            self.bridge_max_duration = None
            self.bridge_cost = None
        
        self.all_ice = game.get_all_icebergs()
        if self.bu_ice != None:
            self.all_ice.append(self.bu_ice)

        self.penguins_to_dest = {}

        self.turn_skope = turn_skope # 50
        self.density = density

        # initialize the penguins_to_dest dictionary;
        for ice in self.all_ice:
            self.penguins_to_dest[ice] = []

        # add the groups heading to the destination;
        for group in game.get_all_penguin_groups():
            self.penguins_to_dest[group.destination].append(group)

        
    def Update(self, game):
        """
        This function initiallizes my ice with the Ice_Info class;
        and updates all of their parameters;
        
        """
    
        self.my_ice = [Ice_Info(game, ice) for ice in game.get_my_icebergs()]
        for ice in self.my_ice:
            ice.Initialize()


    def Get_Attackers(self):
        """
        This function returns all the attackers(via roles);
        """
        ret = []
        for my in self.my_ice:
            if my.is_attacker:
                ret.append(my)

        return ret


    def Get_Supporters(self):
        """
        This function returns all the supporters(via roles);
        """
        ret = []
        for my in self.my_ice:
            if not my.is_attacker:
                ret.append(my)

        return ret


class Ice_Info:
    """
    This class represnts our icebergs with unique parameters;

    The parameters:
        ice             - the iceberg represents;
        amount          - the current amount of penguins an iceberg have(after sending penguins;)
        production      - the production of this iceberg
        level           - the level of the iceberg
        upgrade_cost    - the upgrade cost of this iceberg
        
        max_send        - the maximum number of penguins the iceberg can send;
        is_attacker     - True if an iceberg is an attacker otherwise false(supporter);    
        sp              - the strategic potential of the iceberg;
    """
    def __init__(self, game, ice):
        # constant iceberg parameters
        self.ice = ice
        self.amount = ice.penguin_amount
        self.production = ice.penguins_per_turn
        self.level = ice.level
        self.upgrade_cost = ice.upgrade_cost
        
        # other calculated parameters
        self.max_send = 0
        self.is_attacker = False
        self.sp = 0

        self.dis_from_en = 0


    def Initialize(self):
        """
        This function initializes all the parameters;
        """
        self.Initialize_SP()
        self.Update_Max_Send()
        self.Initialize_Dis_From_En()

    def Initialize_Dis_From_En(self):
        total_dis = 0.0
        for en in turnfo.en_ice:
            total_dis += en.get_turns_till_arrival(self.ice)
        
        self.dis_from_en = total_dis / len(turnfo.en_ice)

    def Initialize_SP(self):
        self.sp = SP(self.ice)
    

    def send_penguins(self, destination, amount):
        if isinstance(destination, Ice_Info):
            self.ice.send_penguins(destination.ice,amount)
        else:
            self.ice.send_penguins(destination,amount)


    def get_turns_till_arrival(self, target):
        if isinstance(target, Ice_Info):
            return self.ice.get_turns_till_arrival(target.ice)
        else:
            return self.ice.get_turns_till_arrival(target)

    def Update_Max_Send(self, turns=50, ice=None):
        """
        This function calculates the amount of penguins that an iceberg can send without getting;
        executen or trying to commit suicide;

        The parameters:
            binary search parameters:
                mini    - the minimum that the iceberg can send (zero at first);
                maxi    - the maximum that the iceberg can send (iceberg penguin amount);
                avg     - the avrege between mini & maxi;
        """
        mini = 0.0
        maxi = self.amount + 1.0
        avg = 0

        avgs = []
        # while we didnt got the same avg twice;
        while avg not in avgs:
            # if called from ice_info else called from outside;
            if ice == None:
                result = Get_Amount(self.ice, turns, offset=avg)[0]
            else:
                result = Get_Amount(ice, turns, offset=avg)[0]
            # if we will die;
            if result <= 0:
                maxi = avg
            else: # we survive;
                mini = avg

            avgs.append(avg)
            avg = math.floor((maxi + mini) / 2)

        if ice == None:
            self.max_send = min(self.ice.penguin_amount, int(avg))
        else:
            self.max_send = min(ice.penguin_amount, int(avg))

        return self.max_send


    def __repr__(self):
        """
        This function overrides the default to_string function of a class;
        """
        #return 'ice:{},is attacker:{}'.format(self.ice ,self.is_attacker)
        return 'ice:{}'.format(self.ice)


class Attack_Info:
    """
    This class represents the unique attack information;

    The Parameters:
        group       - the intended icebergs that will attack the enemy/neutrial iceberg;
        target      - the enemy/neutrial iceberg to attack;

        cost        - the amount of penguins to execute the target + 1;
        can_execute - the amount of turns until the group can attack;
        
        turns       - the maximum turns from the furthest iceberg in the group to the target;
        potential   - the potential of the amount of penguins that can be earned by overtaking;
                    minus the penguins that were used to execute(the cost);
    """
    def __init__(self, group, target, turns, can_execute, cost):

        self.group = group 
        self.target = target

        self.cost = cost
        self.can_execute = can_execute

        self.turns = turns
        self.potential = 0
        
        if self.target != turnfo.bu_ice:    # if the target isn't a bonus iceberg;
            self.potential += PP(self.target.penguins_per_turn, self.turns, self.cost) + SP(self.target)

        else:   #the target is a bouns iceberg
            a = float(turnfo.bonus) / float(turnfo.max_turns_to_bonus) * float(len(turnfo.my_ice)) # bouns production
            if turnfo.bu_ice.owner.id == turnfo.my_id:  # if the bonus iceberg is already ours (defence)
                self.potential += PP(a, turnfo.bu_ice.turns_left_to_bonus, self.cost) + SP(self.target)
            else:   # conquering the bonus
                self.potential += PP(a, self.turns + turnfo.bu_ice.max_turns_to_bonus, self.cost) + SP(self.target)
            
            print("bonus PP: ", self.potential)

        # preferes taking action on non-natrual & bonus icebergs
        # TODO: ??? HUH?? T_T 8==D
#        if self.target.owner.id != -1 and self.target != turnfo.bu_ice:
 #           self.potential += PP(target.penguins_per_turn, self.turns, 0) * 0.5

    def __repr__(self):
        """
        The functions returns a string that contains all of the class parameters(=ToString() in other language)
        """
        return "group:{},target:{},cost:{},can_execute:{},turns:{},group_ptential:{},SP:{}".format(self.group,
                                                                                                self.target,
                                                                                                self.cost,
                                                                                                self.can_execute,
                                                                                                self.turns,
                                                                                                self.potential,
                                                                                                (SP(self.target)))


    def custom_pp(self, cost):
        """
        returns the potential for the singular iceberg in the group to attack/defend
        """
        if self.target == turnfo.bu_ice:
            a = ((turnfo.bonus + 0.0) / (turnfo.bu_ice.turns_left_to_bonus + 0.1)) * len(turnfo.my_ice)
            a -= ((turnfo.bonus + 0.0) / (turnfo.bu_ice.turns_left_to_bonus + 0.1)) * len(turnfo.en_ice)
            return PP(a, self.turns, cost)

        return PP(self.target.penguins_per_turn, self.turns, cost) + SP(self.target)


def PP(a, b, c):
    """
    This function will calculate the Penguin Potential for each possible move
    P(t) = a(t - b) - c
    where: 
        a = penguins per turn gained
        b = turns till gaining
        c = cost to make the move
    """
    return (a * (turn_skope - b) - c)


def Update_Density():
    global density
    density = 0

    maxi_one = 0
    maxi_two = 0

    for ice in turnfo.all_ice:
        for ice2 in turnfo.all_ice:
            if ice.get_turns_till_arrival(ice2) > maxi_one:
                maxi_one = ice.get_turns_till_arrival(ice2)
            elif ice.get_turns_till_arrival(ice2) > maxi_two:
                maxi_two = ice.get_turns_till_arrival(ice2)
            
            if maxi_one < maxi_two:
                temp = maxi_one
                maxi_one = maxi_two
                maxi_two = temp
    
    area = float((maxi_one / 2) * (maxi_two / 2) * math.pi)    # area of an ellipse
    density = float(len(turnfo.all_ice)) / area

def Update_Turn_Skope():
    global turn_skope

    turn_skope = 0
    for ice in turnfo.all_ice:
        turns = Max_Turns_Ice(turnfo.all_ice, ice)
        if turns > turn_skope:
            turn_skope = turns

    turn_skope = turn_skope + 10


def Max_Turns_Ice(iceberg_group, target):
    """
    Returns the amount of turns for the furthest iceberg in a group to get to the target

    The parameters:
        max_turns   - the amount of turns for the furthest iceberg to get to the target
    """
    max_turns = 0

    for iceberg in iceberg_group: 
        turns = iceberg.get_turns_till_arrival(target) 
        if turns > max_turns:
            max_turns = turns
    
    return max_turns


def Max_Turns_En_Penguin(target):  
    """
    Returns the amount of turns for the furthest iceberg in a group to get to the target

    The parameters:
        max_turns   - the amount of turns for the furthest iceberg to get to the target
    """
    max_turns = 0

    for group in turnfo.penguins_to_dest.get(target,[]): 
        if group.owner.id != turnfo.en_id:
            continue

        turns = group.turns_till_arrival
        if turns > max_turns:
            max_turns = turns
    
    return max_turns


def Max_Turns_Penguin(target):  
    """
    Returns the amount of turns for the furthest iceberg in a group to get to the target

    The parameters:
        max_turns   - the amount of turns for the furthest iceberg to get to the target
    """
    max_turns = 0

    for group in turnfo.penguins_to_dest.get(target,[]): 
        turns = group.turns_till_arrival
        if turns > max_turns:
            max_turns = turns
    
    return max_turns

def Normalize_For_SP(turns, max_turns):
    """
        Returns the normalized input data to between 0 to 1 - [0,1] to math lovers
        based on:
            max_turns   - the max distance between the target ice and each iceberg
            turns       - the distance between the target ice and a specific iceberg
            min_turns   - 0 as distance is always grater than zero

            so the formula says:
                (turns - min_turns) / (max_turns - min_turns)
    """
    return (1.0 - (float(turns) / float(max_turns))) ** 2

# :(
# R.I.P magic number
# You will always be remebered! :D
    
        
def SP(ice):
    """
    This fun function calculates <3
    Test: **2
    """
    sp = 0.0
    max_turns = Max_Turns_Ice([iceb for iceb in turnfo.all_ice if iceb != turnfo.bu_ice],ice)
    

    for iceberg in turnfo.my_ice:
        if ice == iceberg.ice: 
            sp += iceberg.amount
            continue
        normalized = Normalize_For_SP(iceberg.ice.get_turns_till_arrival(ice), max_turns)
        sp += float(iceberg.amount) * normalized
    
    for iceberg in turnfo.en_ice:
        if ice == iceberg: 
            continue
        
        normalized = Normalize_For_SP(ice.get_turns_till_arrival(iceberg), max_turns)
        sp -= float(iceberg.penguin_amount) * normalized

    return sp # * (1 + density)


def Max_Send(turns=turn_skope, ice=None, offset = 0):
    # under test
    mini = 0.0
    maxi = float(ice.penguin_amount) - offset + 1 
    avg = 0.0

    avgs = []
    while avg not in avgs:
        result = Get_Amount(ice, turns, offset=avg)[0]
        
        if ice.owner.id == turnfo.my_id:
            if result <= 0:
                maxi = avg
            else:
                mini = avg
        
        else:
            if result >= 0:
                maxi = avg
            else:
                mini = avg

        avgs.append(avg)
        avg = math.floor((maxi + mini) / 2)

        # print('avg',avg,'mini',mini,'maxi',maxi)
    # place for printing
    # print('pa',self.ice.penguin_amount)

    max_send = min(ice.penguin_amount, int(avg))

    return max_send


def The_Nosha(target, turns, beta=0):
    """
    
    """
    cost = beta  # beta
    # cost += Get_Cost(game, target, turns) #gama
    prod = 0
    if target != turnfo.bu_ice:
        prod = target.penguins_per_turn

    for ice in turnfo.en_ice:
        max_send = Max_Send(turns = turns, ice = ice)  # alpha
        enemy_distance_delta = turns - ice.get_turns_till_arrival(target)  # delta phi
        if max_send < abs(min(enemy_distance_delta, 0)) * prod:
            continue
        cost += max_send + min(enemy_distance_delta, 0) * prod
        print('cost:',cost,'target:',target)


    return cost


def The_Nosha_But_Working(target, turns,beta = 0):
    cost = beta
    dist = turns
    for ice in turnfo.en_ice:
        if ice.get_turns_till_arrival(target) < dist:
            cost += Max_Send(turns=turns,ice=ice)
    #/(^.^)/ :D
    return cost 
    

def Get_Cost(target, turns):
    """
    Returns the amount of peguins needed to execute the targeted iceberg
    Input Parameters:
        game    - game board turn parameter
        turns   - the amount of turns to get the furthest icebergs in a group to the target
        target  - the targeted iceberg to be executen

    The parameters:
        cost    - the amount of penguins needed to execute the targeted iceberg
        neutral - a boolean regarding if the target iceberg will stay neutrial after "turns" turns
                regarding the penguin groups targeting the iceberg
    """

    if target == turnfo.bu_ice:
        return 10000000000 + 1 #FRICK YOU BONUS ICE...E
    
    #if the target is an enemy iceberg
    if target.owner.id == turnfo.en_id:
        # get the amount of penguigns that will be on the iceberg atfer 'turns' turns;
        cost = Get_Amount(target, turns)[0]
        if cost > 0:
            return 0 #if we will overtake the island

        #cost += The_Nosha(target,turns,cost)
        return abs(cost) + 1 # add +1 to execute with 1 remaing penguin;
    

    #if the target is a neutrial iceberg
    elif target.owner.id == -1: 
        # get the amount of penguigns that will be on the iceberg atfer 'turns' turns;
        cost, neutral = Get_Amount(target, turns)

        if cost < 0: #the neutral iceberg will be executen by the enemy with 'cost' penguins;
            return abs(cost) + 1

        elif neutral: #the target iceberg will stay neutrial
            return cost + 1 # add +1 to execute with 1 remaing penguin;

    elif target.owner.id == turnfo.my_id: #The target is an ally iceberg
        cost, neutral = Get_Amount(target, turns)
        if cost < 0: #the neutral iceberg will be executen by the enemy with 'cost' penguins;
            return abs(cost) + 1

    return 0 # 
    
        
def Best_Group_Attack(target, forbidden_ice = []):
    """
    Returns the best group combination for an attack;
    ATTACK TTACK TACK ACK SYN ACK
    """
    best_group = None
    best_turns = 1000

    attackers = turnfo.Get_Attackers()
    for i in range(1, len(attackers) + 1):
        for group in itertools.combinations(attackers, i):
            
            if any(item in forbidden_ice for item in group): #if any of the icebergs in the group are forbidden
                continue

            turns_to_execute = Turns_To_Execute_Attack(group, target) #get the time we will have enough penguins to attack;
            if turns_to_execute == 10000:
                continue

            current_turns = turns_to_execute + Max_Turns_Ice(group, target) #include the distance from the group to the target;

            if current_turns < best_turns:
                best_group = group
                best_turns = current_turns
                best_turns_to_execute = turns_to_execute
 
    if best_group == None:
        return None
    
    if best_group[0].ice.id == 1 and len(best_group) == 1:
        print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    return Attack_Info(group = best_group,
                    target = target,
                    turns = best_turns,
                    can_execute = best_turns_to_execute,
                    cost= Get_Cost(target, best_turns))


def Best_Group_Defence(target, forbidden_ice = None):
    """
    Returns the best group combination for an attack;
    ATTACK TTACK TACK ACK SYN ACK
    Only UDP!
    """

    best_group = None
    best_turns = 1000

    defenders = turnfo.my_ice

    removed_ice = None
    for ice in turnfo.my_ice:
        if ice.ice == target:
            defenders.remove(ice)
            removed_ice = ice

    for i in range(1, len(defenders) + 1):
        for group in itertools.combinations(defenders, i):
            if any(item in forbidden_ice for item in group): #if any of the icebergs in the group are forbidden
                continue

            turns_to_execute = Turns_To_Execute_Defence(group, target) #get the time we will have enough penguins to attack;
            current_turns = turns_to_execute + max(Max_Turns_Ice(group,target),Max_Turns_Penguin(target)) #include the distance from the group to the target;
            #checks if the current PP is the best up until now and the icebergs in the group were not used to upgrade/build bridges;
            if current_turns < best_turns: #the shiton
                best_group = group
                best_turns = current_turns
                best_turns_to_execute = turns_to_execute
                
    if best_group == None:
        return None

    
    cost = Get_Cost(target, best_turns+1)
    #if cost == 0:
        
    defenders.append(removed_ice)
    #we keep it for dvir
    #I know he is full of smoke
    del removed_ice

    return Attack_Info(group=best_group,
                    target=target,
                    turns=best_turns,
                    can_execute=best_turns_to_execute,
                    cost= cost)               


def Turns_To_Execute_Attack(attacking_icebergs, target):
    """
    Returns one of three status when trying to execute an iceberg with a group;
    
    Input Parameters:
        attacking_icebergs  - the group of the icebergs that attack;
        target              - the target

    where:
        return 0        - The group has enough penguins to execute;
        return 1000     - the group will never be able to execute;
        return x        - the group will take x turns to have enough to execute;

    The parameters:
        total_production    - the total production of all icebergs in group;
        total_amount        - the total amount of all current peguins in group;
        
        en_production       - the production of the targeted iceberg;
        
        max_turns           - the biggest distance from each iceberg in the group to the targeted iceberg;
        cost                - the amount of peguins needed to execute the targeted iceberg;
                            with 1 remaining penguin ;
    """

    total_production = float(0)
    total_amount = float(0)

    en_production = 0
    
    if target != turnfo.bu_ice:
        en_production = target.penguins_per_turn
        
    
    max_turns = Max_Turns_Ice(attacking_icebergs, target)
    cost = Get_Cost(target, max_turns)

    for ice_info in attacking_icebergs:
        total_production += ice_info.ice.penguins_per_turn
        total_amount += ice_info.max_send


    if total_amount >= cost:
        return 0 # we can attack!;

    elif total_production > en_production:
        return int(math.ceil((cost - total_amount) / float(total_production - en_production)))

    return 10000


def Turns_To_Execute_Defence(defending_icebergs, target):
    """
    Returns one of three status when trying to execute an iceberg with a group
    where:
        return 0        - the group has this turn at least the amount of penguins to execute
        return -1000    - the group will never be able    
        return x        - the group will take x turn to have enough to execute

    The parameters:
        total_production    - the total production of all icebergs in group
        total_amount        - the total amount of all current peguins in group
        en_production       - the production of the targeted iceberg 
        max_turns           - the biggest distance from each iceberg in the group to the targeted iceberg
        cost                - the amount of peguins needed to execute the targeted iceberg
                            with 1 remaining penguin 
    """

    total_production = float(0)
    total_amount = float(0)
    max_turns = max(Max_Turns_Penguin(target),Max_Turns_Ice(defending_icebergs,target))

    cost = Get_Cost(target, max_turns)
    #print('target:',target,'cost:',cost)
    for ice_info in defending_icebergs:
        total_production += ice_info.ice.penguins_per_turn
        total_amount += ice_info.max_send
    

    if total_amount >= cost:
        return 0

    return int(math.ceil((cost - total_amount) / float(total_production)))


def Assign_Roles(attackers = 2):
    """
    This function determines which icebergs are attackers and supporters by the strategic potential;
    """
    my_ice = turnfo.my_ice
    my_ice = sorted(my_ice, key = lambda ice:ice.dis_from_en)
    for ice in my_ice[:attackers]:
        ice.is_attacker = True
    
    for ice in my_ice[attackers:]:
        ice.is_attacker = False
    
    
def Calculate_bridge_impact(penguin_group,bridge_duration):
    """
    This function calculates the new distance for a penguin group with a bridge depending on it's duration
    """
    
    dis = penguin_group.turns_till_arrival # hashoora;
    dis -= turnfo.bridge_multi * bridge_duration
    
    if dis < 0:
        return int(math.ceil(float(penguin_group.turns_till_arrival) / float(turnfo.bridge_multi)))
        
    else:
        return dis + bridge_duration
    

def Update_Penguin_Group_TTA(ice, sources = None):
    """
    This function updates all the turns till arrival of the penguins group that on bridges;
    and supports "simulating" bridges to check if we want to build a bridge;

    Input Parameters:
        ice     - the targeted ice that we want to update the time of arrival of the penguin groups targeting it;
        sources - the sources of whom we want to build bridges from (ice can't be in sources);
    """
    if sources == None:
        sources = []

    incoming_penguin_groups = turnfo.penguins_to_dest.get(ice,[]) #return all the incoming penguin groups headed to ice;
    # a list containing tuples with (penguin group, distance with current bridge/if the suorces in sources[] had a bridge/distance without current bridge)
    updated_till_arrival = []
    for penguin_group in incoming_penguin_groups:
        #print('ice:',ice,'sources',sources)
        if ice.bridges != []:
            for bridge in ice.bridges:
                if penguin_group.source in bridge.get_edges():
                    #if the penguin group is on a bridge
                    updated_till_arrival.append((penguin_group, Calculate_bridge_impact(penguin_group,bridge.duration)))
                    break
            
            #the targeted ice has bridges, but this group is not on a bridge
            else:
                #we want to build a bridge there so we will add it
                if penguin_group.source in sources:
                    updated_till_arrival.append((penguin_group,Calculate_bridge_impact(penguin_group,turnfo.bridge_max_duration)))
                
                #we don't want to build a bridge there
                else:
                    updated_till_arrival.append((penguin_group, penguin_group.turns_till_arrival))

        #the targeted ice doesn't have bridges 
        #but we want to build a bridge to this penguin group
        elif sources != [] and penguin_group.source in sources:
            updated_till_arrival.append((penguin_group,Calculate_bridge_impact(penguin_group,turnfo.bridge_max_duration)))
        
        #the targeted ice doesn't have bridges 
        #and we don't want to build a bridge to this penguin group
        else:
            updated_till_arrival.append((penguin_group, penguin_group.turns_till_arrival)) 
        

    return updated_till_arrival
    
def Lo_Yodaat(left, updated_till_arrival, index):
    total_ally = 0
    total_en = 0
    neutral = True
    i = index
    for ii in range(index,len(updated_till_arrival) - 1):
        if updated_till_arrival[ii][0].owner.id == turnfo.my_id:
            total_ally += updated_till_arrival[ii][0].penguin_amount
        else:
            total_en -= updated_till_arrival[ii][0].penguin_amount # <3
        
        if updated_till_arrival[ii][1] != updated_till_arrival[ii+1][1]:
            i = ii #?????????????!?!?!?!?!?!?!?!?!?!?!?!?! ;P
            break
        
        i = ii
    else:
        if updated_till_arrival[-1][0].owner.id == turnfo.my_id:
            total_ally += updated_till_arrival[-1][0].penguin_amount
        else:
            total_en -= updated_till_arrival[-1][0].penguin_amount # <3
        i = len(updated_till_arrival)

    if total_ally != 0 and total_en != 0:
        if total_ally - total_en > left:
            
            left = total_ally + total_en
            #print(left,i,updated_till_arrival)
            if left != 0:   
                return left, False, i , True
            return left, True, i , True
        else:
            i = index
    else:
        i = index
    # remove the sent penguins from the nutrual
    left -= updated_till_arrival[i][0].penguin_amount
    if left < 0:    # if there has been a takeover >:)
        if updated_till_arrival[i][0].owner.id == turnfo.my_id:  # this is our takeover!!!!!!!!!!!!!!
            left = abs(left)    # lovelyyyyyyy
        neutral = False

    return left, neutral, i , False

def Get_Amount(ice, turns, offset = 0, bridge_sources=[]):
    """
    hapkooda!
    Gets an iceberg
    Returns the amount of penguins present in an iceberg after a certain amount of turns
    if left < 0: ENEMY penguin amount (negative)
    if left > 0: FRIENDLY penguin amount (positive)
    Where:
        turns   - how deep to look (in turns);
        ice     - the iceberg to check the saftey of;
        return  - left;
    """

    updated_till_arrival = Update_Penguin_Group_TTA(ice, bridge_sources)    # new ttls via bridges :)
    updated_till_arrival = sorted(updated_till_arrival, key = lambda x : x[1], reverse = False) # sort from closest to furthest;

    #print('GET AMOUNTTTT','ice',ice,'uta', updated_till_arrival)

    neutral = False
    if ice.owner.id == turnfo.my_id:
        left = ice.penguin_amount #if our iceberg left is positive;
    elif ice.owner.id == turnfo.en_id:
        left = -ice.penguin_amount #if enemy left is negative;
    else:
        left = ice.penguin_amount - offset #if neutral left positive and neutral set to True;
        neutral = True

    ice_prod = 0
    if ice != turnfo.bu_ice:
        ice_prod = ice.penguins_per_turn

    if ice.owner.id == turnfo.en_id:
        left = -ice.penguin_amount  + offset
    elif ice.owner.id == turnfo.my_id:
        left = ice.penguin_amount - offset
        try:
            if left == 0 and not updated_till_arrival[0].turns_till_arrival == 1:
                left += ice_prod
                last_turns = 1
        except:
            left += ice_prod
            last_turns = 1

    last_turns = 0   # the amount of turns already passed;
    i = 0
    while i < len(updated_till_arrival):
        penguin_group, turns_till_arrival = updated_till_arrival[i]
        #if ice.id == 4 and bridge_sources == []:
        #    print(left,neutral, i, updated_till_arrival[i],'In While')
     
        if turns_till_arrival > turns:
            break

        if not neutral:
            #if we have the iceberg;
            if left > 0:
                # append that shit
                left += ice.penguins_per_turn * (turns_till_arrival - last_turns)
            # the iceberg is the emeny's
            else:
                # append that shit but do it negatively
                left -= ice.penguins_per_turn * (turns_till_arrival - last_turns)
        
        if not neutral: # do it again :(
            # if it's our penguin group
            if penguin_group.owner.id == turnfo.my_id:
                left += penguin_group.penguin_amount    # positiveeeeeee
            # the enemy's stupid penguin group
            else:
                left -= penguin_group.penguin_amount    # negativeeeeee
        
        #habahur nutrualelelelel
        else:
            #print('target',ice,'group',penguin_group,'BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')
            left, neutral, i, flag = Lo_Yodaat(left,updated_till_arrival,i)
            #if ice.id == 4 and bridge_sources == [] and flag:
            #    print(left,neutral, i, updated_till_arrival)
            if flag:
                i += 1
                last_turns = turns_till_arrival
                continue

        if left == 0:   # she's a nutrual again :( :D
            neutral = True
        
        last_turns = turns_till_arrival # DONE! SO PRETTY!
        
        i += 1
    
    #if ice.id == 4 and bridge_sources == []:
    #    print(left,neutral,'Out While')

    if not neutral:
        if left > 0:
            left += ice.penguins_per_turn * (turns - last_turns)
        else:
            left -= ice.penguins_per_turn * (turns - last_turns)

    else:
        left = abs(left)

    return left, neutral


def Turns_To_Upgrade(ice):
    useable_amount = float(ice.max_send)
    upgrade_cost = ice.upgrade_cost
    if upgrade_cost <= useable_amount:
        return 0

    return math.ceil((upgrade_cost - useable_amount) / ice.production)
    

def Upgrade(attack_infos, ice_used):
    # if it's better to upgrade, upgrade. then, find second best option for the attack
    global density
    
    attacking_ices = set()
    upgraded_infos = []
    
    for i, attack in enumerate(attack_infos):
        for ice in attack.group:
            if ice in ice_used or ice.level == 4:
                continue
            
            print('attacking ice',attacking_ices,'ice',ice)
            turns_to_upgrade = Turns_To_Upgrade(ice)
            upgrade_PP = (1-density) * PP(1, turns_to_upgrade, ice.upgrade_cost) + SP(ice.ice)  # the upgrade potential for an iceberg
            amount = Attack_Split(attack, ice)  # the amount that this iceberg will attack in this attack info
            attack_potential = attack.custom_pp(amount)  # calculates the attack potential of this iceberg
            if len(attack.group) == 1: attack_potential = attack.potential
            
            print('ice:', ice.ice, 'upgrade_PP:', upgrade_PP, 'attack_PP:', attack_potential,'amount:', amount,'SP',SP(ice.ice))
            if upgrade_PP >= attack_potential and ice not in attacking_ices:
                ice_used.add(ice)
                if ice.max_send > ice.ice.upgrade_cost:
                    ice.ice.upgrade()
                    upgraded_infos.append(i)
                    break
            else:
                attacking_ices.add(ice)

        if attack != None:
            for ice in attack.group:
                attacking_ices.add(ice)

    not_attackers = [ice_info for ice_info in turnfo.my_ice if ice_info not in attacking_ices]
    for ice in turnfo.my_ice:
        if ice.level == 4:
            continue
        if ice not in ice_used and ice.max_send > ice.upgrade_cost:
            ice.ice.upgrade()
            ice_used.add(ice)
    
    for index in upgraded_infos:
        if attack.target.owner.id == turnfo.my_id:
            attack_infos[index] = Best_Group_Defence(attack.target, forbidden_ice=ice_used)
        else:
            attack_infos[index] = Best_Group_Attack(attack.target, forbidden_ice=ice_used)


    return attack_infos, ice_used

def Attack_Split(attack_info, my_ice):
    """
    Returns the amount that each iceberg needs to send in a group in attack_info

    Input Parameters:
        game            - gameboard turn object
        attack_info     - all of the information about an attack(check AttackInfo class)

    The Parameters:
        group           - an array that contains all of the icebergs in the attacking group
        left_to_send    - contains the cost of the attack minus the amount that each iceberg 
                        attacks with, so how much more needed to send in order to send the full cost
        amount          - the amount for each iceberg to send
    """
    group = []
    for ice_info in attack_info.group:
        group.append(ice_info)

    # sort by the lowest startegic rating to the best to that the lower the startegic cost
    # the more the iceberg sends
    group.sort(key=lambda x: x.level, reverse=True)

    left_to_send = attack_info.cost
    for ice_info in group:
        amount = min(left_to_send, ice_info.max_send)
        left_to_send -= amount
        if ice_info.ice == my_ice.ice:
            return amount


def Attack_And_Defence(attack_info):
    """
    """
    
    attackers = attack_info.group
    attackers = sorted(attackers, key = lambda ice : ice.level, reverse = True) # from furtest to closest
    
    need_to_send = attack_info.cost
    max_group_turns = Max_Turns_En_Penguin(attack_info.target)
    for attacker in attackers:
        
        attack_amount = int(min(need_to_send, attacker.max_send))
        need_to_send -= attack_amount

        dist = attacker.get_turns_till_arrival(attack_info.target)
        print('--------') # $_$ 
        print('group:', attackers)
        print('amount:', attack_amount)
        print('target', attack_info.target)
        print('turns:', attack_info.turns)
        print('cost:', attack_info.cost)
        print('--------')

        best_attack_group = [attacker]
        if dist <= max_group_turns:
            for i in range(1,len(attackers) + 1):
                for attack_group in itertools.combinations(attackers,i):
                    attack_amount = sum([attackeron.amount for attackeron in attack_group])
                    if Get_Amount(attack_info.target,attack_info.turns,offset=attack_amount)[1] > 0:
                        best_attack_group = attack_group

        for att in best_attack_group:
            att.ice.send_penguins(attack_info.target, attack_amount)
            att.amount -= attack_amount
            att.Update_Max_Send()


def Already_Taken_Action(target):
    """
    Returns whether the existing pengiuin groups on the board will execute
    the target(if the target will be ours) 
    where:
        return False    - the target will not be ours
        return True     - the target will be ours

    """
    if Get_Cost(target,turnfo.turn_skope):
        return False
    return True
    

def Closest_Attacker(supporter):
    attackers = turnfo.Get_Attackers()
    
    sorted_attackers = sorted(attackers, key = lambda ice: (ice.level,ice.get_turns_till_arrival(supporter)))
    closest_attacker = sorted_attackers[0]
    
    return closest_attacker


def Support(ice_used):
    supporters = turnfo.Get_Supporters()

    for supporter in supporters:
        if supporter.max_send < 4 or supporter in ice_used:
            continue

        if supporter.level == 4 and supporter not in ice_used:
            supporter.send_penguins(Closest_Attacker(supporter), supporter.max_send)

def Is_There_A_Bridge(edge1, edge2):
    """
    Checks if there's an existing bridge between the two given icebergs (edge1, edge2)
    """
    if edge1.bridges == []:
        return False
    
    for bridge in edge1.bridges:
        if edge2 in bridge.get_edges():
            return True
    
    return False

def Bridge_Reinforcement(game,ice_used):
    bridge_dests = turnfo.all_ice
    print(game.get_time_remaining())
    if game.get_time_remaining() < -50:
        bridge_dests = turnfo.en_ice

    for target in bridge_dests:
        # can't build bridges to bonus ice
        if target == turnfo.bu_ice:
            continue

        penguin_groups = turnfo.penguins_to_dest.get(target,[]) # all the penguin groups which are headed for the target
        group_ids = [group.owner.id for group in penguin_groups]
        # if all the penguin groups are the enemy's
        if turnfo.my_id not in group_ids:
            continue

        # a dictionary connecting between the source of the penguin groups and the groups     
        sources = {} # {s1:[penguingroup0,penguingroup1],s2:[penguingroup2]}
        
        for group in penguin_groups:
            # the group isn't ours and isn't relevent
            if group.owner.id != turnfo.my_id:
                continue
            # connect the penguin groups to the source
            if sources.get(group.source,[]) != []:
                sources[group.source].append(group)
            else:
                sources[group.source] = [group]
        
        # for all the possible source combinations (bridges group)
        best_group = None
        best_PP = 0
        for group_len in range(1, len(sources) + 1):
            for group in itertools.combinations(sources,group_len):

                flag = True
                for ice in group:
                    # there's already a bridge
                    if Is_There_A_Bridge(ice,target):
                        flag = False
                        break
                    # there aren't enough penguins to build a bridge from the source
                    if Max_Send(turn_skope,ice) < turnfo.bridge_cost:
                        flag = False
                        break
                if not flag:
                    continue
                
                #if we don't defend/overtake with the bridge then it doesn't help >:(
                #print("-----------GET AMOUNT BRIDGE----------")
                amount, neutral = Get_Amount(target, turn_skope,bridge_sources=group)
                #print("-----------GET AMOUNT BRIDGE----------")
                if amount < 0 or neutral:
                    continue
                
                updated_ally_penguin_groups = [g[1] for g in Update_Penguin_Group_TTA(target,group) if g[0].owner.id == turnfo.my_id]
                max_turns_with_bridges = max(updated_ally_penguin_groups)
                # potential with bridge
                current_PP = PP(target.penguins_per_turn, max_turns_with_bridges, len(group) * turnfo.bridge_cost)
                if current_PP > best_PP:
                    #print(target,max_turns_with_bridges)
                    best_group = group
                    best_PP = current_PP
        
        
        updated_ally_penguin_groups = [g[1] for g in Update_Penguin_Group_TTA(target) if g[0].owner.id == turnfo.my_id]
        normal_max_turns = max(updated_ally_penguin_groups)
        current_PP = 0
        
        if Get_Cost(target,turn_skope) == 0:
            current_PP = PP(target.penguins_per_turn,normal_max_turns,0)    # the potential without the bridge
        else:
            current_PP = PP(0,normal_max_turns,0)   # the potential of abandoning the iceberg(0)
        
        if target.owner.id == turnfo.my_id:
            for attacker in turnfo.Get_Attackers():
                #print('if:',att=cker.ice == target,Max_Send(turns = max_turns , ice = target) > 0,'target:',target,'group',best_group)
                if attacker.ice == target and Max_Send(turns = normal_max_turns , ice = target) > 0:
                    flag = True
            if flag:
                continue
        #print('bridge PP', best_PP,'without bridge PP', current_PP)
        # if building a bridge will be better
        if best_PP > current_PP:
            for ice in best_group:
                ice.create_bridge(target)
                for ice_info in turnfo.my_ice:
                    if ice_info.ice == ice:
                        ice_used.add(ice_info)
                        break
    return ice_used


def attackers_amount():
    a = float(len(turnfo.my_ice))
    #return int(math.ceil((1.0 - ((1 / density) / 100.0)) * a))
    #return int(math.ceil((1.0 - density) * a/2))
def do_turn(game):
    
    global turnfo, turn_skope, density
    print(density)
    turnfo = Game_Info(game)
    turnfo.Update(game)

    if game.turn == 1:
        Update_Turn_Skope()
        Update_Density()

    #aa = attackers_amount()
    Assign_Roles(attackers=3)

    attack_infos = []
    ice_used = set()

    print('Skope: ', turn_skope)
    print('desnsity:',density)
    print('Attackers: ', turnfo.Get_Attackers())

    ice_used = Bridge_Reinforcement(game,ice_used)
    
    #for ice in turnfo.my_ice:
    #    print('MAX_SEND: ', ice.max_send,';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;')
    
    for ice in turnfo.all_ice:
        best_group = None

        #print("-----------------------")
        if ice.owner.id == -1 and ice != turnfo.bu_ice:
            #print('NEUTRAL: ',ice,'Already_Taken_Action:',Already_Taken_Action(ice),'get amount',Get_Amount(ice, turn_skope))
            pass
        if ice.owner.id == turnfo.my_id:
            #print('MY:',ice,'Already_Taken_Action:',Already_Taken_Action(ice),'get amount',Get_Amount(ice, turn_skope))
            pass
        #else:
        #    print('ENEMY: ', ice,Get_Amount(ice, turn_skope))

        #print("SP: ", SP(ice))
        #print("Already Taken Action: ", Already_Taken_Action(ice))

        if ice == turnfo.bu_ice:
            continue

        if Already_Taken_Action(ice):  # if the defence / attack task is already taken care of
            continue
        
        if ice.owner.id != turnfo.my_id:
            best_group = Best_Group_Attack(ice, ice_used)
        else:
            best_group = Best_Group_Defence(ice, ice_used)

        if best_group == None:
            continue

        attack_infos.append(best_group)
    # shiton week 3 The if
    if len(turnfo.my_ice) == 1 and density == 0.01695141405712495:
        if Max_Send(turns = 50, ice = turnfo.my_ice[0].ice,offset = turnfo.en_ice[0].penguin_amount) <= 0:
            return
        
    attack_infos = sorted(attack_infos, key = lambda x: x.potential, reverse = True) #from best 8=========D to worst
    attack_infos, ice_used = Upgrade(attack_infos,ice_used)
    attack_infos = [info for info in attack_infos if info != None]
    attack_infos = sorted(attack_infos, key = lambda x: x.potential, reverse = True) #from best 8=========D to worst


    for attack in attack_infos:
        
        if attack.target.owner.id == turnfo.my_id:
            attack.can_execute = Turns_To_Execute_Defence(attack.group, attack.target)
            print('Defence:', attack)

        else:
            #get the time we will have enough penguins to attack;
            attack.can_execute = Turns_To_Execute_Attack(attack.group, attack.target)
            print('Attack:', attack)

        if attack.potential < 0:
            break
            
        if attack.can_execute > 0:
            for iceberg in attack.group:
                ice_used.add(iceberg)
            continue
        
        for ice_info in attack.group:
            if ice_info in ice_used:
                break
        else:
 
            Attack_And_Defence(attack)

    Support(ice_used)
    print('ICE USED',ice_used)
    print(game.get_time_remaining())

    
#  The End 

"""
By:
    Shoshani Hashoshana
    Dvir Hamadbir :D
    Pepperoni Pizza
    Maya :P
"""
