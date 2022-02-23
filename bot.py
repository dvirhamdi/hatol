from penguin_game import *
import math
import itertools

# global variable for saving the game's given parameters;
turnfo = None
#determins the density of the icebergs in the map;
density = 0

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


    my_prod - our total prodaction;
    en_prod - enemy total prodaction;
    
    penguins_to_dest    - dictionary of the penguins groups aheding to a iceberg[dict];
                        dict format: {ice1:[group1,group3],ice2:[],ice3:[group2],...}
    
    bridge_multi    - the speed multiplayer the bridge provides;
    bridge_max_duration - the maximum turns the bridge will last;

    K   -   turns depth (start, end, step);
    density - the density of the map;
    
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
        
        self.my_prod = 0.0
        self.en_prod = 0.0

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
        except AttributeError:
            self.bridge_multi = None
            self.bridge_max_duration = None
        
        self.all_ice = game.get_all_icebergs()
        if self.bu_ice != None:
            self.all_ice.append(self.bu_ice)

        self.penguins_to_dest = {}

        self.K = (49, 50, 1)  # turns depth (start, end, step);

        self.density = density

        # initialize the penguins_to_dest dictionary;
        for ice in self.all_ice:
            self.penguins_to_dest[ice] = []

        # add the groups heading to the destination;
        for group in game.get_all_penguin_groups():
            self.penguins_to_dest[group.destination].append(group)

        self.Update_My_Porduction(game)
        self.Update_En_Porduction(game)

        
    def Update(self, game, attackers=2):
        """
        This function initiallizes my ice with the Ice_Info class;
        and updates all of their parameters;
        
        """
        self.my_ice = [Ice_Info(game, ice) for ice in game.get_my_icebergs()]

        for ice in self.my_ice:
            ice.Update_All(attackers=attackers)


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
    

    def Update_My_Porduction(self, game):
        """
        This function updates our total production;
        """
        for ice in game.get_my_icebergs():
            self.my_prod += ice.penguins_per_turn
        
        #calculates the bonus iceberg production;
        if self.bu_ice != None and self.bu_ice.owner.id == self.my_id:
            self.my_prod += (float(self.bonus) / float(self.bu_ice.max_turns_to_bonus)) * len(game.get_my_icebergs())
    
    
    def Update_En_Porduction(self, game):
        """
        This function updates the total enemy production;
        """
        for ice in game.get_enemy_icebergs():
            self.en_prod += ice.penguins_per_turn

        #calculates the bonus iceberg production;
        if self.bu_ice != None and self.bu_ice.owner.id == self.en_id:
            self.my_prod += (float(self.bonus) / float(self.bu_ice.max_turns_to_bonus)) * len(self.en_ice)


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

    def Update_All(self, attackers = 2):
        """
        This function updates all the parameters;
        """
        self.Update_Role(attackers = attackers)
        self.Update_Max_Send()
        self.Update_SP()


    def Update_SP(self):
        self.sp = SP(self.ice)


    def Update_Role(self, attackers = 2):
        Assign_Roles(attackers=attackers)


    def Update_Max_Send(self, turns=50, ice=None):
        """
        This function calculates the amount of penguins that an iceberg can send without getting;
        overtaken or trying to commit suicide;

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
                result = Get_Amount(self.ice, turns, offset=avg)
            else:
                result = Get_Amount(ice, turns, offset=avg)
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
        return str(self.ice)


class Attack_Info:
    """
    This class represents the unique attack information;

    The Parameters:
        group       - the intended icebergs that will attack the enemy/neutrial iceberg;
        target      - the enemy/neutrial iceberg to attack;

        cost        - the amount of penguins to overtake the target + 1;
        can_execute - the amount of turns until the group can attack;
        
        turns       - the maximum turns from the furthest iceberg in the group to the target;
        potential   - the potential of the amount of penguins that can be earned by overtaking;
                    minus the penguins that were used to overtake(the cost);
    """
    def __init__(self, group, target, turns, can_execute, cost):

        self.group = group 
        self.target = target

        self.cost = cost
        self.can_execute = can_execute

        self.turns = turns
        self.potential = 0
        
        #if the target is an enemy and our total production is greater then lower the potential;
        if self.target.owner.id == turnfo.en_id and turnfo.my_prod >= turnfo.en_prod:
            self.potential -= float(turnfo.en_prod/turnfo.my_prod) * 10.0
        if self.target != turnfo.bu_ice:    # if the target isn't a bonus iceberg;
            self.potential += PP_avg(self.target.penguins_per_turn, self.turns, self.cost) + SP(target)

        else:   #the target is a bouns iceberg
            
            #TODO:need to be better!!!
            a = float(turnfo.bonus) / float(turnfo.max_turns_to_bonus) * float(len(turnfo.my_ice)) # bouns prod
            print("bonus a:", a)
            if turnfo.bu_ice.owner.id == turnfo.my_id:
                self.potential = PP_avg(a, self.turns + turnfo.bu_ice.turns_left_to_bonus, self.cost) #no sp??
            else:
                self.potential = PP_avg(a, self.turns + turnfo.bu_ice.max_turns_to_bonus, self.cost) # no so??
                if turnfo.bu_ice.owner.id == -1:
                    self.potential -= SP(self.target) #???
            
            """if turnfo.bu_ice.owner.id == turnfo.en_id:
                a = float(turnfo.bonus) / float(turnfo.bu_ice.max_turns_to_bonus) * float(len(turnfo.en_ice))
                self.potential += PP_avg(a, self.turns, self.cost)"""
            print("bonus PP:", self.potential)
            
            """a = ((turnfo.bonus + 0.0) / (turnfo.bu_ice.turns_left_to_bonus + 0.1)) * len(turnfo.my_ice)
            a -= ((turnfo.bonus + 0.0) / (turnfo.bu_ice.turns_left_to_bonus + 0.1)) * len(turnfo.en_ice)

            print('a', a, turnfo.bonus, turnfo.bu_ice.turns_left_to_bonus, len(turnfo.my_ice),
                (turnfo.bonus / (turnfo.bu_ice.turns_left_to_bonus + 0.1)))
            self.potential = PP_avg(a, self.turns, self.cost) + SP(target)

            a = ((turnfo.bonus + 0.0) / (turnfo.bu_ice.turns_left_to_bonus + 0.1)) * len(turnfo.my_ice)  # our prod
            a -= ((turnfo.bonus + 0.0) / (turnfo.bu_ice.turns_left_to_bonus + 0.1)) * len(turnfo.en_ice) 

            if turnfo.bu_ice.id == turnfo.en_id:
                self.potential += PP_avg(a, self.turns, 0) * 0.5"""
            

        # if the iceberg isn't neutral & the target isn't a bonus iceberg
        if self.target.owner.id != -1 and self.target != turnfo.bu_ice:
            # dis = 0
            # calculate the mean distance from all the icebergs
            # for ice in turnfo.all_ice:
            #    for ice2 in turnfo.all_ice:
            #        dis += ice2.get_turns_till_arrival(ice)

            #    dis /= len(turnfo.all_ice)

            self.potential += PP_avg(target.penguins_per_turn, self.turns, 0) * 0.5


    def __repr__(self):
        return "group:{},target:{},cost:{},can_execute:{},turns:{},group_ptential:{},SP:{}".format(self.group,
                                                                                                self.target,
                                                                                                self.cost,
                                                                                                self.can_execute,
                                                                                                self.turns,
                                                                                                self.potential,(SP(
                                                                                                        self.target)))


    def custom_pp(self, cost):
        """
        returns the potential for the singular iceberg in the group to attack/defend
        """
        if self.target == turnfo.bu_ice:
            a = ((turnfo.bonus + 0.0) / (turnfo.bu_ice.turns_left_to_bonus + 0.1)) * len(turnfo.my_ice)
            a -= ((turnfo.bonus + 0.0) / (turnfo.bu_ice.turns_left_to_bonus + 0.1)) * len(turnfo.en_ice)
            return PP_avg(a, self.turns, cost)

        return PP_avg(self.target.penguins_per_turn, self.turns, cost) + SP(self.target)


def Assign_Roles(attackers = 2):
    sorted_my = sorted(turnfo.my_ice, key=lambda ice_info: ice_info.sp, reverse=False)
    for ice in sorted_my[:attackers]:
        ice.is_attacker = True

    for ice in sorted_my[attackers:]:
        ice.is_attacker = False


def SP(ice):
    """
    This function returns the startegic potential of an iceberg
    The furthest iceberg from the enemy will have the highest SP.
    When the map is denser the SP is less important.
    """
    
    avg_dist = 0.0   # average destenation between the iceberg and the enemy icebergs
    for ice2 in turnfo.en_ice:
        avg_dist += ice.get_turns_till_arrival(ice2)    
    avg_dist /= len(turnfo.en_ice)
    #print(avg_dist * density / 100.0)
    return float(avg_dist) * float(density)

    
def Max_Send(turns=50, ice=None):
    # under test
    mini = 0.0
    maxi = float(ice.penguin_amount) + 1
    avg = 0

    avgs = []
    while avg not in avgs:
        result = Get_Amount(ice, turns, offset=avg)
        if result <= 0:
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


def Get_Amount(ice, turns, offset=0):
    """
    hpkoda!
    returns the amount of penguins present in a friendly iceberg after (turns)
    if left < 0: ENEMY penguin amount (negative)
    if left > 0: FRIENDLY penguin amount (positive)
    Where:
        turns   - how deep to look (in turns);
        ice     - the friendly iceberg to check the saftey of;
        return  - left;
    """
    
    #get all penguins heading to ice;
    groups = turnfo.penguins_to_dest.get(ice, [])
    #sort by distance: closest to furthest;
    groups.sort(key = lambda x:x.turns_till_arrival)
    
    ice_prod = 0
    if ice != turnfo.bu_ice:
        ice_prod = ice.penguins_per_turn
        
    #save the turns of the last group
    last_turns = 0
    #amount of penguins left on ice;
    if ice.owner.id == turnfo.en_id:
        left = -ice.penguin_amount  + offset
    else:
        left = ice.penguin_amount - offset
        try:
            if left == 0 and not groups[0].turns_till_arrival == 1:
                left += ice_prod
                last_turns = 1
        except:
            left += ice_prod
            last_turns = 1
    
    turns_before_bonus = 0
    passed_turns_to_bonus = False
    for group in groups:
        till_arrival = group.turns_till_arrival
        if ice.bridges != []:
            for bridge in ice.bridges:
                #if the iceberg is the destination and the penguin group on the bridge;
                if bridge.get_edges()[1] == ice and group.source == bridge.get_edges()[0]:
                    till_arrival = math.floor(group.turns_till_arrival / float(bridge.speed_multiplier))
                    if till_arrival > bridge.duration:
                        till_arrival += group.turns_till_arrival - (bridge.duration * bridge.speed_multiplier)
        #if we left the turn scope: exit
        if till_arrival > turns:
            break
        
        turns_passed = till_arrival - last_turns
        turns_before_bonus += turns_passed



        if left > 0:
            left += ice_prod * (till_arrival - last_turns)
            turns_passed = till_arrival - last_turns

        elif left < 0:
            left -= ice_prod * (till_arrival - last_turns)
            if turnfo.bu_ice.owner.id == turnfo.en_id:# check if it's the enemy's bonus iceberg
                # if the bonus will have an influence  
                if not passed_turns_to_bonus and turns_before_bonus >= turnfo.bu_ice.turns_left_to_bonus:
                    left -= turnfo.bu_ice.penguin_bonus     # adding the bonus
                    turns_before_bonus -= turnfo.bu_ice.turns_left_to_bonus  # turns left utill next bonus 
                    passed_turns_to_bonus = True
                    
                if passed_turns_to_bonus and turns_before_bonus >= turnfo.bu_ice.max_turns_to_bonus:
                    left -= turnfo.bu_ice.penguin_bonus * math.floor(turns_before_bonus/turnfo.bu_ice.max_turns_to_bonus)
                    turns_before_bonus -= turnfo.bu_ice.max_turns_to_bonus * math.floor(turns_before_bonus/turnfo.bu_ice.max_turns_to_bonus)
        
        if group.owner.id == turnfo.my_id:
            left += group.penguin_amount      
        else:
            left -= group.penguin_amount

        last_turns = till_arrival

    if left > 0:
        left += ice_prod * (turns - last_turns)
    else:
        left -= ice_prod * (turns - last_turns)

    return left


def Get_Amount_Neutral(ice, turns):
    global penguins_to_dest
    """
    returns the amount of penguins present in a friendly iceberg after (turns)
    if left < 0: ENEMY penguin amount (negative)
    if left > 0: FRIENDLY penguin amount (positive)
    Where:
        game    - game object;
        turns   - how deep to look (in turns);
        ice     - the friendly iceberg to check the saftey of;
        return  - left;
    """

    # get penguins heading to ice;
    groups = turnfo.penguins_to_dest.get(ice, [])

    # sort by distance: closest to furthest;
    groups.sort(key=lambda x: x.turns_till_arrival)

    # amount of penguins left on ice;
    left = ice.penguin_amount
    neutral = True
    iceberg_prod = 0

    if ice != turnfo.bu_ice:
        iceberg_prod = ice.penguins_per_turn

    # save the turns_till_arrival of the last group;
    last_turns = 0

    for group in groups:
        till_arrival = group.turns_till_arrival

        # if left turn scope: exit;
        if till_arrival > turns:
            break

        if neutral:
            left -= group.penguin_amount
            if left < 0:
                neutral = False
                if group.owner.id == turnfo.my_id:
                    left = abs(left)

        else:
            if left > 0:
                left += iceberg_prod * (till_arrival - last_turns)

            elif left < 0:
                left -= iceberg_prod * (till_arrival - last_turns)

            if group.owner.id == turnfo.my_id:
                left += group.penguin_amount

            else:
                left -= group.penguin_amount

            if left == 0:
                neutral = True

        last_turns = till_arrival

    if not neutral:
        if left > 0:
            left += iceberg_prod * (turns - last_turns)
        else:
            left -= iceberg_prod * (turns - last_turns)

    return left, neutral


def PP(t, a, b, c):
    """
    This function will calculate the Penguin Potential for each possible move
    P(t) = a(t - b) - c
    where: 
        a = penguins per turn gained
        b = turns till gaining
        c = cost to make the move
    """
    return (a * (t - b) - c)


def PP_avg(a, b, c):
    total_PP = 0.0
    K = turnfo.K

    for t in range(K[0], K[1], K[2]):
        total_PP += PP(t, a, b, c)

    return total_PP / ((K[1] - K[0]) / K[2])


def The_Nosha(target, turns, beta=0):
    cost = beta  # beta
    # cost += Get_Cost_Attack(game, target, turns) #gama
    prod = 0
    if target != turnfo.bu_ice:
        prod = target.penguins_per_turn

    for ice in turnfo.en_ice:
        max_send = Max_Send(turns=turns, ice=ice)  # alpha
        enemy_distance_delta = turns - ice.get_turns_till_arrival(target)  # delta phi
        if max_send < abs(min(enemy_distance_delta, 0)) * prod:
            continue
        cost += max_send + min(enemy_distance_delta, 0) * prod
        # print('cost:',cost,'target:',target)

    return cost


def Get_Cost_Attack(target, turns):
    global ally_id
    global enemy_id
    """
    Returns the amount of peguins needed to overtake the targeted iceberg
    Input Parameters:
        game    - game board turn parameter
        turns   - the amount of turns to get the furthest icebergs in a group to the target
        target  - the targeted iceberg to be overtaken

    The parameters:
        cost    - the amount of penguins needed to overtake the targeted iceberg
        neutral - a boolean regarding if the target iceberg will stay neutrial after "turns" turns
                regarding the penguin groups targeting the iceberg
    """

    if target.owner.id == turnfo.en_id:
        cost = abs(Get_Amount(target, turns))
        return cost + The_Nosha(target, turns) + 1

    elif target.owner.id == -1:
        cost, neutral = Get_Amount_Neutral(target, turns)
        cost += The_Nosha(target, turns)

        if not neutral and cost <= 0:
            return abs(cost) + 1

        return cost + 1


def Get_Cost_Defence(target, turns):
    """
    Returns the amount of peguins needed to overtake the targeted iceberg
    Input Parameters:
        game    - game board turn parameter
        turns   - the amount of turns to get the furthest icebergs in a group to the target
        target  - the targeted iceberg to be overtaken

    The parameters:
        left    - the amount of penguins left in the targeted iceberg after "turns" turns
    """

    left = Get_Amount(target, turns)
    if left > 0:  # if the iceberg will already be ours then increase it's costs by 1000!
        return 1000

    # print('left',(left),'target:',target)
    return abs(left) + 1


def Turns_To_Execute_Attack(group, target):
    """
    Returns one of three status when trying to overtake an iceberg with a group
    where:
        return 0        - the group has this turn at least the amount of penguins to overtake
        return 1000    - the group will never be able    
        return x        - the group will take x turn to have enough to overtake

    The parameters:
        total_production    - the total production of all icebergs in group
        total_amount        - the total amount of all current peguins in group
        en_production       - the production of the targeted iceberg 
        max_turns           - the biggest distance from each iceberg in the group to the targeted iceberg
        cost                - the amount of peguins needed to overtake the targeted iceberg
                            with 1 remaining penguin 
    """

    total_production = float(0)
    total_amount = float(0)
    en_production = 0
    if target != turnfo.bu_ice:
        en_production = target.penguins_per_turn
    max_turns = Max_Group_Turns(group, target)
    cost = Get_Cost_Attack(target, max_turns)

    for ice_info in group:
        total_production += ice_info.ice.penguins_per_turn
        total_amount += ice_info.max_send


    if total_amount >= cost:
        return 0

    elif total_production > en_production:
        return int(math.ceil((cost - total_amount) / float(total_production - en_production)))

    return 1000


def Turns_To_Execute_Defence(group, target):
    """
    Returns one of three status when trying to overtake an iceberg with a group
    where:
        return 0        - the group has this turn at least the amount of penguins to overtake
        return -1000    - the group will never be able    
        return x        - the group will take x turn to have enough to overtake

    The parameters:
        total_production    - the total production of all icebergs in group
        total_amount        - the total amount of all current peguins in group
        en_production       - the production of the targeted iceberg 
        max_turns           - the biggest distance from each iceberg in the group to the targeted iceberg
        cost                - the amount of peguins needed to overtake the targeted iceberg
                            with 1 remaining penguin 
    """

    total_production = float(0)
    total_amount = float(0)
    max_turns = Max_Group_Turns(group, target)
    cost = Get_Cost_Defence(target, max_turns)

    for ice_info in group:
        total_production += ice_info.ice.penguins_per_turn
        total_amount += ice_info.max_send


    if total_amount >= cost:
        return 0

    return int(math.ceil((cost - total_amount) / float(total_production)))


def Max_Group_Turns(group, target):
    """
    Returns the amount of turns for the furthest iceberg in a group to get to the target

    The parameters:
        max_turns   - the amount of turns for the furthest iceberg to get to the target
    """

    max_turns = 0
    for ice_info in group:
        turns = ice_info.ice.get_turns_till_arrival(target)
        if turns > max_turns:
            max_turns = turns

    return max_turns


def Best_Group_Attack(target, forbidden_ice=[]):
    """
    Returns the best group combination for an attack
    """
    best_group = None
    best_turns = 1000

    attackers = turnfo.Get_Attackers()
    for i in range(1, len(attackers) + 1):
        for group in itertools.combinations(attackers, i):
            turns_to_overtake = Turns_To_Execute_Attack(group, target)
            current_turns = turns_to_overtake + Max_Group_Turns(group, target)
            if current_turns < best_turns and not any(item in forbidden_ice for item in group):
                best_group = group
                best_turns = current_turns
                best_turns_to_overtake = turns_to_overtake

    if best_group == None:
        return None

    return Attack_Info(group=best_group,
                    target=target,
                    turns=best_turns,
                    can_execute=best_turns_to_overtake,
                    cost=Get_Cost_Attack(target, Max_Group_Turns(best_group, target)))


def Best_Group_Defence(target, forbidden_ice=[]):
    """
    Chooses the best group combination for a defence
    TODO: I need to be better!
    """
    best_group = None
    best_turns = 1000

    defenders = sorted(turnfo.my_ice, key=lambda x: x.is_attacker)

    for i in range(1, len(defenders) + 1):
        for group in itertools.combinations(defenders, i):
            turns_to_overtake = Turns_To_Execute_Defence(group, target)
            current_turns = turns_to_overtake + Max_Group_Turns(group, target)
            if current_turns < best_turns and not any(item in forbidden_ice for item in group):
                best_group = group
                best_turns = current_turns
                best_turns_to_overtake = turns_to_overtake

    if best_group == None:
        return None

    return Attack_Info(group=best_group,
                    target=target,
                    turns=best_turns,
                    can_execute=best_turns_to_overtake,
                    cost=Get_Cost_Defence(target, Max_Group_Turns(best_group, target)))


def Attack(attack_info, ice_used):
    """
    Attacks a target with the iceberg group while each icebergs attacks 
    based on the number of penguins it has

    The parameters:
        total   - the total amount of penguins in the group
    """
    group = []
    for ice_info in attack_info.group:
        group.append(ice_info)
    group.sort(key=lambda x: x.sp, reverse=True)

    left_to_send = attack_info.cost


    for ice_info in group:
        amount = min(left_to_send, ice_info.max_send)
        left_to_send -= amount
        print('---------------')
        print('group:', group)
        print('amount:', amount)
        print('target', attack_info.target)
        print('turns:', Max_Group_Turns(group, attack_info.target), 'target:', attack_info.target)
        print('cost:', attack_info.cost)
        print('---------------')
        ice_info.ice.send_penguins(attack_info.target, int(amount))
        #ice_used.add(ice_info)
        ice_info.amount -= int(amount)
        ice_info.Update_Max_Send()




def Attack_Split(attack_info, my):
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
    group.sort(key=lambda x: x.sp, reverse=False)

    left_to_send = attack_info.cost
    for ice_info in group:
        amount = min(left_to_send, ice_info.max_send)
        left_to_send -= amount
        if ice_info.ice == my.ice:
            return amount


def Already_Taken_Action(target):
    """
    Returns whether the existing pengiuin groups on the board will overtake
    the target(if the target will be ours) 
    where:
        return False    - the target will not be ours
        return True     - the target will be ours

    """
    if target.owner.id == -1:
        left, neutral = Get_Amount_Neutral(target, 50)
        if neutral:
            return False
        if left <= 0:
            return False

        return True

    if Get_Amount(target, 50) <= 0:
        return False

    return True


def Turns_To_Upgrade(ice):
    useable_amount = ice.max_send + 0.0
    upgrade_cost = ice.upgrade_cost
    if upgrade_cost < useable_amount:
        return 0

    return math.ceil((upgrade_cost - useable_amount) / ice.production)


def Upgrade(attack_infos, ice_used):
    # if it's better to upgrade, upgrade. then, find second best option for the attack
    attacking_ices = []

    for i, attack in enumerate(attack_infos):
        for ice in attack.group:
            if ice in ice_used or ice.level == 4:
                continue
            turns_to_upgrade = Turns_To_Upgrade(ice)
            upgrade_PP = PP_avg(1, turns_to_upgrade, ice.upgrade_cost) + SP(ice.ice)  # the upgrade potential for an iceberg
            amount = Attack_Split(attack, ice)  # the amount that this iceberg will attack in this attack info
            attack_potential = attack.custom_pp(amount)  # calculates the attack potential of this iceberg
            if len(attack.group) == 1: attack_potential = attack.potential
            
            print('ice:', ice.ice, 'upgrade_PP:', upgrade_PP, 'attack_PP:', attack_potential,'amount:', amount)
            if upgrade_PP > attack_potential and ice not in attacking_ices:
                ice_used.add(ice)
                if ice.max_send > ice.ice.upgrade_cost:
                    ice.ice.upgrade()

                    if attack.target.owner.id == turnfo.my_id:
                        attack_infos[i] = Best_Group_Defence(attack.target, forbidden_ice=ice_used)
                    else:
                        attack_infos[i] = Best_Group_Attack(attack.target, forbidden_ice=ice_used)
                    break

        if attack != None:
            attacking_ices = attacking_ices + [ice for ice in attack.group]

    for ice in turnfo.my_ice:
        if ice.level == 4:
            continue
        if ice not in ice_used and ice.max_send > ice.upgrade_cost:
            ice.ice.upgrade()
            ice_used.add(ice)


    return attack_infos, ice_used


def Support(ice_used):
    """
    
    """
    for support in turnfo.Get_Supporters():
        attackers = sorted(turnfo.Get_Attackers(),key = lambda x: x.ice.get_turns_till_arrival(support.ice))
        if support not in ice_used and support.level >= 3:
            if support.level == 3:
                print('hereeeeeeee')
                support.ice.send_penguins(attackers[0].ice,min(support.max_send,2))
            else:
                print('hereeeeeeee22222')
                support.ice.send_penguins(attackers[0].ice,support.max_send)


def Bridge_Reinforcement(game, ice_used):

    if game.get_time_remaining() > -150: # protection from timeout;
        unally = turnfo.all_ice
    else:
        unally = turnfo.nu_ice + turnfo.en_ice 

    for target in unally:
        if target == turnfo.bu_ice: # can't build bridges to bonus iceberg;
            continue
        
        #if there is an ally group heading to target;
        group_ids = [group.owner.id for group in turnfo.penguins_to_dest[target]]
        if turnfo.my_id not in group_ids:
            continue

        groups = turnfo.penguins_to_dest[target]
        sources = {}    # containing the connection between the source icebergs and the penguin groups from them;

        for group in groups:
            #if the penguin group is an enemy's group bye bye bitch;
            if group.owner.id == turnfo.en_id:
                continue
            # if the source can't pay for a bridge;
            if Max_Send(turns=50, ice = group.source) < group.source.bridge_cost:
                continue
            
            #initialize sources dictionary;
            if sources.get(group.source,[]) == []:
                sources[group.source] = [group]
            else:
                sources[group.source].append(group)    
                
        
        best_PP = 0 # the best PP found;
        best_group = None #the best paths to make a bridge in;
        
        #finds the best combination of bridges;
        for i in range(1, len(sources) + 1):    # for all the iceberg sources;
            for group in itertools.combinations(sources, i):    # finds the best bridge + penguin groups combination;
                flag = False
                for ice in group:
                    if ice.bridges:
                        print('ice',ice)
                        print('bridges',ice.bridges)
                        print('edges',ice.bridges[0].get_edges())
                        for bridge in ice.bridges:
                            if bridge.get_edges() == (ice,target):
                                flag = True
                                break
                    if flag:
                        break
                if flag:
                    continue
                #if building the bridge will help;
                gab = Get_Amount_Bridge(target,turnfo.K[1],group)
                #print('Get_amount with bridge:',gab,'target:',target,'sources:',sources)
                amount, neutral = gab
                if amount > 0 and not neutral:
                    
                    total_turns = [] # a list containing all of the turns_till_arival of the groups to the destination(including the bridges);
                    # for all the penguin groups heading to the target;

                    #add the amount of turns the attack/defence will take on total with the bridge; 
                    for g in turnfo.penguins_to_dest[target]:
                        if g.source not in group:  # if the penguin group isn't sent from the bridge source;
                            total_turns.append(g.turns_till_arrival)
                            continue
                        
                        # calculate the number of turns needed while using the bridge;
                        dis = g.turns_till_arrival # hashora;
                        dis -= turnfo.bridge_multi * turnfo.bridge_max_duration
                        if dis < 0:
                            total_turns.append(turnfo.bridge_max_duration + math.floor(dis/turnfo.bridge_multi))
                        else:
                            total_turns.append(dis + group[0].max_bridge_duration)
                        print("turns with bridge:", total_turns[-1],'penguin group:',g,'source:',g.source,'target:',g.destination)
                    
                    current_PP = PP_avg(a = target.penguins_per_turn, b = max(total_turns), c = len(group) * group[0].bridge_cost) #bridge pp;
                    if current_PP > best_PP:
                        best_PP = current_PP
                        best_group = group
        
        if best_group == None:
            continue
        
        max_turns = sorted(turnfo.penguins_to_dest[target],key = lambda x: x.turns_till_arrival)[-1].turns_till_arrival # hashora;
        if target.owner.id == turnfo.my_id:
            for attacker in turnfo.Get_Attackers():
                #print('if:',att=cker.ice == target,Max_Send(turns = max_turns , ice = target) > 0,'target:',target,'group',best_group)
                if attacker.ice == target and Max_Send(turns = max_turns , ice = target) > 0:
                    flag = True
            if flag:
                continue
        # if only the penguin groups will help;
        if Get_Amount(target,turns=turnfo.K[1]) > 0:
            print('BPP:','group:',best_group,'target:',target,'bridge_PP:',best_PP)
            # if the potential with the bridge is larger than the potential with only the penguin groups;
            if best_PP >= PP_avg(target.penguins_per_turn,max_turns, 0):
                for ice in best_group:
                    ice_info = None
                    # finding the ice_info
                    for ice2 in turnfo.my_ice:
                        if ice2.ice == ice:
                            ice_info = ice2
                            break
                    if ice_info not in ice_used:
                        ice.create_bridge(target)
                        ice_used.add(ice_info)
        # if only the penguin groups won't help -> see if a bridge would make the group helpful;
        else:
            print('BPP2:','group:',best_group,'target:',target,'bridge_PP:',best_PP)
            # if the potential with the bridge is larger than giving up;
            if best_PP >= PP_avg(0, max_turns, 0):
                for ice in best_group:
                    ice_info = None
                    # finding the ice_info
                    for ice2 in turnfo.my_ice:
                        if ice2.ice == ice:
                            ice_info = ice2
                            break
                        
                    if ice_info not in ice_used:
                        ice.create_bridge(target)
                        ice_used.add(ice_info)

    return ice_used
                    

def Get_Amount_Bridge(target, turns , bridge_sources):

    groups = turnfo.penguins_to_dest[target]
    #get all penguins heading to ice
    groups.sort(key = lambda x:x.turns_till_arrival)
    
    ice_prod = 0
    if target != turnfo.bu_ice:
        ice_prod = target.penguins_per_turn
        
    neutral = True if target.owner.id == -1 else False
    #save the turns of the last group
    last_turns = 0
    #amount of penguins left on ice
    if target.owner.id == turnfo.en_id:
        left = -target.penguin_amount 
    else:
        left = target.penguin_amount
        try:
            if left == 0 and not groups[0].turns_till_arrival == 1:
                left += ice_prod
                last_turns = 1
        except:
            left += ice_prod
            last_turns = 1
    
    turns_before_bonus = 0
    passed_turns_to_bonus = False
    for group in groups:
        till_arrival = group.turns_till_arrival
        if target.bridges != []:
            for bridge in target.bridges:
                #if the iceberg is the destination and the penguin group on the bridge
                if bridge.get_edges()[1] == target and group.source == bridge.get_edges()[0]:
                    till_arrival = math.floor(group.turns_till_arrival / float(bridge.speed_multiplier))
                    if till_arrival > bridge.duration:
                        till_arrival += group.turns_till_arrival - (bridge.duration * bridge.speed_multiplier)
        
        if group.source in bridge_sources:
            till_arrival = math.floor(group.turns_till_arrival / float(group.source.bridge_speed_multiplier))
            if till_arrival > group.source.max_bridge_duration:
                till_arrival += group.turns_till_arrival - (group.source.max_bridge_duration * group.source.bridge_speed_multiplier)
        
        if neutral:
            left -= group.penguin_amount
            if left < 0:
                neutral = False
                if group.owner.id == turnfo.my_id:
                    left = abs(left)
            else:
                continue
                

        #if we left the turn scope: exit
        if till_arrival > turns:
            break
        
        turns_passed = till_arrival - last_turns
        turns_before_bonus += turns_passed

        if left > 0:
            left += ice_prod * (till_arrival - last_turns)
            turns_passed = till_arrival - last_turns

        elif left < 0:
            left -= ice_prod * (till_arrival - last_turns)
            if turnfo.bu_ice.owner.id == turnfo.en_id:# check if it's the enemy's bonus iceberg
                # if the bonus will have an influence  
                if not passed_turns_to_bonus and turns_before_bonus >= turnfo.bu_ice.turns_left_to_bonus:
                    left -= turnfo.bu_ice.penguin_bonus     # adding the bonus
                    turns_before_bonus -= turnfo.bu_ice.turns_left_to_bonus  # turns left utill next bonus 
                    passed_turns_to_bonus = True
                    
                if passed_turns_to_bonus and turns_before_bonus >= turnfo.bu_ice.max_turns_to_bonus:
                    left -= turnfo.bu_ice.penguin_bonus * math.floor(turns_before_bonus/turnfo.bu_ice.max_turns_to_bonus)
                    turns_before_bonus -= turnfo.bu_ice.max_turns_to_bonus * math.floor(turns_before_bonus/turnfo.bu_ice.max_turns_to_bonus)            
        

        if group.owner.id == turnfo.my_id:
            left += group.penguin_amount      
        else:
            left -= group.penguin_amount

        last_turns = till_arrival

    if left > 0:
        left += ice_prod * (turns - last_turns) 
    elif left < 0:
        left -= ice_prod * (turns - last_turns)
    else:
        neutral = True

    return left , neutral

def Update_density():
    
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
    
    area = (maxi_one / 2) * (maxi_two / 2) * math.pi    # area of an ellipse
    density = (math.sqrt(len(turnfo.all_ice) / area))
    print('desnsity:',density)

def do_turn(game):
    global turnfo

    turnfo = Game_Info(game)
    turnfo.Update(game, attackers=3)
    if game.turn == 1:
        Update_density()
    attack_infos = []  # an array of all of the attack infos of the best groups

    ice_used = set()  # a set containing all icebergs that have done an action(upgraded/attacked)

    #print("Attackers,", turnfo.Get_Attackers())
    

    ice_used = Bridge_Reinforcement(game, ice_used) # calculate bridge uses
    # we get the attack infos of the best groups
    for ice in turnfo.all_ice:
        #if ice.owner.id == turnfo.my_id:
            #print("FRIENDLY_ICE: ", ice, Get_Amount(ice, 50))
            # print("MAX_SEND_AMOUNT: ", ice.max_send)
        #elif ice.owner.id == turnfo.en_ice:
            #print("ENEMY_ICE: ", ice, Get_Amount(ice, 50))
        #else:
            #print("NEUTRAL_ICE: ", ice, Get_Amount_Neutral(ice, 50))


        if Already_Taken_Action(ice):  # if there is a penguin group attacking enough already
            continue

        if ice.owner.id == turnfo.my_id:
            best_group = Best_Group_Defence(ice, forbidden_ice=ice_used)

        else:
            best_group = Best_Group_Attack(ice, forbidden_ice=ice_used)

        if best_group != None:
            attack_infos.append(best_group)


    attack_infos.sort(key=lambda x: x.potential, reverse=True)

    # if it's better to upgrade, upgrade. then, find second best option for the attack
    attack_infos, ice_used = Upgrade(attack_infos, ice_used)

    attack_infos = [a for a in attack_infos if a != None]
    attack_infos.sort(key=lambda x: x.potential, reverse=True)

    #print('attack infos ', attack_infos)

    for attack in attack_infos:
        if attack.target in game.get_my_icebergs():
            turns_to_overtake = Turns_To_Execute_Defence(attack.group, attack.target)
            attack.can_execute = turns_to_overtake
            print('Defence: ', attack)
        else:
            turns_to_overtake = Turns_To_Execute_Attack(attack.group, attack.target)
            attack.can_execute = turns_to_overtake
            print('Attack: ', attack)

        # if the group cannat execute the attack this turn then wait
        if attack.can_execute > 0:
            for ice_info in attack.group:
                ice_used.add(ice_info)
            continue

        # checks if there is an iceberg that already acted in this group
        for ice_info in attack.group:
            #print('ice used:', ice_used)
            if ice_info in ice_used:
                break
        else:
            Attack(attack, ice_used)

    Support(ice_used)
    print(game.get_time_remaining())
    #bshvil
    #shoshani hshamen
