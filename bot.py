from penguin_game import *
import itertools
import math

class Attack_Info:
    
    def __init__(self, group, target, turns, can_execute, cost):
        """
        The Parameters:
            group       - the intended icebergs that will attack the enemy/neutrial iceberg
            target      - the enemy/neutrial iceberg to attack
            can_execute - True if the group can attack the target this turn, False otherwise
            cost        - the amount of penguins to overtake the target + 1
            potential   - the potential of the amount of penguins that can be earned by overtaking
            ㅤ            minus the penguins that were used to overtake
        """
        self.group = group      
        self.target = target    
        self.cost = cost    
        self.can_execute = can_execute     
        self.turns = turns
        self.potential = PP_avg(target.penguins_per_turn, self.turns, self.cost)
        if self.target.owner.id != -1:
            self.potential += PP_avg(target.penguins_per_turn, self.turns, 0)
           
    def __repr__(self):
        return "group:{},target:{},cost:{},can_execute:{},turns:{},group_ptential:{}".format(self.group,self.target,self.cost,
        self.can_execute,self.turns,self.potential) 


    def custom_pp(self, cost):
        return PP_avg(self.target.penguins_per_turn, self.turns, cost)


K = (10, 100, 10) # turns depth (start, end, step)


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
    
    for t in range(K[0],K[1],K[2]):
        total_PP += PP(t, a, b, c)

    return total_PP / ((K[1] - K[0]) / K[2])


def SP(game, ice, modifier = 10):
    return Strategic_Rating(game, ice) * modifier


def Strategic_Rating(game, ice):

    turns = 0.0

    for any_ice in game.get_all_icebergs():
        turns += ice.get_turns_till_arrival(any_ice)

    return 1 / (turns / len(game.get_all_icebergs()))


def Penguins_To_Destination(game, target, Id = 0):
    
    ret = []
    
    if Id == 0:
        groups = game.get_my_penguin_groups()
    elif Id == 1:   
        groups = game.get_enemy_penguin_groups()
    elif Id == 2:
        groups = game.get_all_penguin_groups()

    for group in groups:
        if group.destination == target:
            ret.append(group)
    
    return ret


def Penguins_On_Way(groups):
    """
    Returns the amount of penguins that are heading 
    to the target according to id:
        id = 0  - the friendly penguins that are heading to the target
        id = 1  - the enemy penguins that are heading to the target

        The parameters:
            groups  - all penguin groups based on id
            total   - the amount of penguins that are heading to the target
            
    """
    
    total = 0
    
    for group in groups:
            total += group.penguin_amount
    return total


def Enemy_Defence_Power(game, target, turns):
    en_ice = game.get_enemy_icebergs()
    
    en_ice = sorted(en_ice, key = lambda x:x.get_turns_till_arrival(target))

    defence_power = 0

    for ice in en_ice:
        #print('herrreeeeee',target)
        if ice.get_turns_till_arrival(target) > turns:
            break
        
        defence_power += Max_Send_Amount(game, ice, turns)
    print('edp',defence_power + target.penguins_per_turn * turns + 1)
    return defence_power + target.penguins_per_turn * turns + 1


def Get_Cost_Attack(game, target, turns):
    """
    Returns the amount of peguins needed to overtake the targeted iceberg
    Input Parameters:
        game    - game board turn parameter
        turns   - the amount of turns to get the furthest icebergs in a group to the target
        target  - the targeted iceberg to be overtaken
        
    The parameters:
        turns               - the amount of penguins that are needed for the group 
        ㅤ                  to overtake the target
        en_group            - all of the enemy penguins that head to target
        target_production   - the amount of penguins that the targeted iceberg generated(if target icebergs is enemy)

    """


    if target.owner.id == 1:
        #print('target:',target,'enemy def:',Get_Cost_Defence(game, target, turns))
        cost = abs(Get_Amount(game, target, turns)) 
        return cost + 1

    elif target.owner.id == -1: 
        cost, neutral = Get_Amount_Neutral(game, target, turns)
        if not neutral:
            if cost <= 0:
                return abs(cost) + 1 
                    
        return cost + 1        


def Get_Cost_Defence(game, target, turns):
    """
    Returns the amount of peguins needed to overtake the targeted iceberg
    Input Parameters:
        game    - game board turn parameter
        turns   - the amount of turns to get the furthest icebergs in a group to the target
        target  - the targeted iceberg to be overtaken
        
    The parameters:
        turns               - the amount of penguins that are needed for the group 
        ㅤ                  to overtake the target
        en_group            - all of the enemy penguins that head to target
        target_production   - the amount of penguins that the targeted iceberg generated(if target icebergs is enemy)

    """
    left = Get_Amount(game, target, turns)
    if left > 0:
        return 1000
    
    print('left',(left),'target:',target)
    return abs(left) + 1
    
        
def Get_Amount(game, ice, turns, offset = 0):
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
    
    #get all penguins heading to ice;
    groups = Penguins_To_Destination(game, ice, Id = 2)

    #sort by distance: closest to furthest;
    groups.sort(key = lambda x:x.turns_till_arrival)

    #amount of penguins left on ice;
    if ice.owner.id == 1:
        left = -ice.penguin_amount + offset 
    else:
        left = ice.penguin_amount - offset 

    #save the turns of the last group
    last_turns = 0
    
    for group in groups:
        till_arrival = group.turns_till_arrival
        #print('dleft:',left,'ice',ice)
        #if we left the turn scope: exit
        if till_arrival > turns:
            break

        if left > 0:
            left += ice.penguins_per_turn * (till_arrival - last_turns)

        elif left < 0:
            left -= ice.penguins_per_turn * (till_arrival - last_turns)

        if group.owner.id == 0:
            left += group.penguin_amount      
        else:
            left -= group.penguin_amount
        last_turns = till_arrival

    if left > 0:
        left += ice.penguins_per_turn * (turns - last_turns)
    else:
       left -= ice.penguins_per_turn * (turns - last_turns)

    return left
    

def Get_Amount_Neutral(game, ice, turns):
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
    
    #get penguins heading to ice;
    groups = Penguins_To_Destination(game, ice, Id = 2)

    #sort by distance: closest to furthest;
    groups.sort(key = lambda x:x.turns_till_arrival)

    #amount of penguins left on ice;
    left = ice.penguin_amount
    neutral = True

    #save the turns_till_arrival of the last group;
    last_turns = 0 
    
    for group in groups:
        till_arrival = group.turns_till_arrival
        if till_arrival > turns:
            break

        if neutral:
            left -= group.penguin_amount
            if left < 0:
                neutral = False
                if group.owner.id == 0:
                    left = abs(left)
                
        else:

            if left > 0:
                left += ice.penguins_per_turn * (till_arrival - last_turns)

            elif left < 0:
                left -= ice.penguins_per_turn * (till_arrival - last_turns)
                
            if group.owner.id == 0:
                left += group.penguin_amount

            else:
                left -= group.penguin_amount
            
            last_turns = till_arrival

    if not neutral:
        if left > 0:
            left += ice.penguins_per_turn * (turns - last_turns)
        else:
            left -= ice.penguins_per_turn * (turns - last_turns)
    
    return left, neutral


def Max_Send_Amount(game, ice, turns = 50):
    """
    """
    mini = float(0)
    if Get_Amount(game, ice, turns) <= 0:
        return 0

    maxi = float(ice.penguin_amount) - 1
    avg = math.ceil((mini + maxi) / 2)
    used = []

    while avg not in used:
        used.append(avg)
        result = Get_Amount(game, ice, turns, offset = avg)

        if ice.owner.id == 0:
            if result < 0:
                maxi = avg
            else:
                mini = avg
        #ice is enemy
        else:
            if result > 0:
                maxi = avg
            else:
                mini = avg

        avg = math.ceil((mini + maxi) / 2)
            

    return int(min(avg + 1, ice.penguin_amount))
    
            
def Turns_To_Execute_Attack(game, group, target):
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
        en_amount           - the current amount of penguins in the targeted iceberg
        cost                - the amount of peguins needed to overtake the targeted iceberg
                              with 1 remaining penguin 
    """
    
    total_production = float(0)
    total_amount = float(0)
    en_production = target.penguins_per_turn
    en_amount = target.penguin_amount
    max_turns =  Max_Group_Turns(group, target)
    cost = Get_Cost_Attack(game, target, max_turns)

    for ice in group:
        total_production += ice.penguins_per_turn
        safe_amount = Max_Send_Amount(game, ice, 50)
        if safe_amount > 0:
            total_amount += safe_amount  
        
    if total_amount >= cost:
        return 0

    elif total_production > en_production:
        return int(math.ceil((cost - total_amount) / float(total_production - en_production)))

    return -1000


def Turns_To_Execute_Defence(game, group, target):
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
        en_amount           - the current amount of penguins in the targeted iceberg
        cost                - the amount of peguins needed to overtake the targeted iceberg
                              with 1 remaining penguin 
    """
    
    total_production = 0
    total_amount = 0
    max_turns = Max_Penguin_Turns(Penguins_To_Destination(game, target, Id = 2))
    cost = Get_Cost_Defence(game, target, max_turns)
    till_cost = 0
    
    for ice in group:
        total_production += ice.penguins_per_turn
        safe_amount = Max_Send_Amount(game, ice, 50)
        if safe_amount > 0:
            total_amount += safe_amount  
        
    if total_amount >= cost:
        return 0
    
    turns_to_execute = int(math.ceil((cost - total_amount) / total_production))
    #print("TurnsToExecute: ", turns_to_execute)
    return turns_to_execute

        
def Max_Group_Turns(group, target):
    """
    Returns the amount of turns for the furthest iceberg to get to the target

    The parameters:
        max_turns   - the amount of turns for the furthest iceberg to get to the target
    """

    max_turns = 0
    for ice in group:
        turns = ice.get_turns_till_arrival(target)
        if turns > max_turns:
            max_turns = turns
    
    return max_turns
        

def Max_Penguin_Turns(groups):
    """
    Returns the amount of turns for the furthest iceberg to get to the target

    The parameters:
        max_turns   - the amount of turns for the furthest penguin group to arrive
    """
    
    max_turns = 0
    for group in groups:
            turns = group.turns_till_arrival
            if turns > max_turns:
                max_turns = turns
    
    return max_turns


def Best_Group(game, target):
    """
    Returns the Attack info of the most optimized group of icebergs to attack
    a target
    Attack_Info contains:
        best_group  - the optimized group to attack the target
        target      - the target of the attack
        best_turns  - the amount of turns to get all of the penguins 
        ㅤ            to the target and for the group to have the amount 
        ㅤ            of penguins to overtake the targe
        GetCost()   - the amount of penguins needed to overtake the target + 1         

    """
    my_ice = game.get_my_icebergs()
    
    best_turns = 1000
    best_group = None
    turns_to_overtake = 0
    best_turns_to_overtake = 0

    for i in range(1, min(len(my_ice) + 1, 3)):
        for group in itertools.combinations(my_ice, i):
            if target.owner.id == 0:
                if target in group:
                    break
                turns_to_overtake = Turns_To_Execute_Defence(game, group, target)
            else:
                turns_to_overtake = Turns_To_Execute_Attack(game, group, target)
            total_turns = turns_to_overtake + Max_Group_Turns(group, target)
            if turns_to_overtake >= 0:
                if total_turns < best_turns:
                    best_turns = total_turns
                    best_group = group
                    best_turns_to_overtake = turns_to_overtake
            
    if best_group == None:
        return None

    #print('cost',Get_Cost_Attack(game, Max_Group_Turns(best_group,target), target),'target',target)
    max_turns = Max_Penguin_Turns(Penguins_To_Destination(game, target, Id = 1))
    #max_turns = max(max_turns,Max_Penguin_Turns(Penguins_To_Destination(game, target, Id = 0)))
    #cost = Get_Cost_Defence(game, target, max_turns)
    if target.owner.id == 0:
        print('max_turns:',max_turns,'target:',target)
        return Attack_Info(group = best_group, 
                        target = target, 
                        turns = best_turns,
                        can_execute = best_turns_to_overtake,
                        cost = Get_Cost_Defence(game, target, max_turns))
                        
    return Attack_Info(group = best_group, 
                        target = target, 
                        turns = best_turns,
                        can_execute = best_turns_to_overtake,
                        cost = Get_Cost_Attack(game, target, Max_Group_Turns(best_group,target)))
        
    
def Attack(game, attack_info, ice_used):
    """
    Attacks a target with the iceberg group while each icebergs attacks 
    based on the number of penguins it has
    
    The parameters:
        total   - the total amount of penguins in the group
    """
    group = []
    for ice in attack_info.group:
        group.append(ice)
    group.sort(key = lambda x:Strategic_Rating(game, x), reverse = True)

    left_to_send = attack_info.cost

    for ice in group:
        amount = min(left_to_send, Max_Send_Amount(game, ice))
        left_to_send -= amount
        print('---------------')
        print('group:', group)
        print('amount:',amount)
        print('target', attack_info.target)
        print('turns:',Max_Group_Turns(group, attack_info.target),'target:',attack_info.target)
        print('cost:',attack_info.cost)
        print('---------------') 
        ice.send_penguins(attack_info.target, int(amount))
        ice_used.add(ice)


def Attack_Split(game, attack_info, my):

    group = []
    for ice in attack_info.group:
        group.append(ice)

    group.sort(key = lambda x:Strategic_Rating(game, x), reverse = False)

    left_to_send = attack_info.cost

    for ice in group:
        amount = min(left_to_send, Max_Send_Amount(game, ice))
        left_to_send -= amount  
        if ice == my:
             return amount


def Already_Taken_Action(game, target):

    if target.owner.id == -1:
        left, neutral = Get_Amount_Neutral(game, target, 50)
        if neutral:
            return False
        if left <= 0:
            return False

        return True

    if Get_Amount(game, target, 50) <= 0:
        return False
        
    return True
  

def do_turn(game):
    """
    dvir.
    smokes......
    """
    
    attack_infos = []
    ice_used = set()

    for ice in game.get_all_icebergs():

        if ice.owner.id == 0:
            print("FRIENDLY_ICE: ", ice, Get_Amount(game, ice, 50))
            print("MAX_SEND_AMOUNT: ", Max_Send_Amount(game, ice))
            pass
        elif ice.owner.id == 1:
            print("ENEMY_ICE: ", ice,  Get_Amount(game, ice, 50))
            pass
        else:
            print("NEUTRAL_ICE: ", ice,  Get_Amount_Neutral(game, ice, 50))
            pass
        if Already_Taken_Action(game, ice):
            continue
        
        my_best_group = Best_Group(game, ice)

        if my_best_group == None:
            continue

        my_best_group.potential += SP(game, ice)
        attack_infos.append(my_best_group)

    #sort the attack infos by potential from best to worst
    attack_infos.sort(key = lambda x:x.potential, reverse = True)
    
    for my in game.get_my_icebergs():

        if my.level == 4:
            continue
        
        upgrade_PP = PP_avg(1, 0, my.upgrade_cost) + SP(game, my)
        
        for attack in attack_infos:
            if my not in attack.group:
                continue
            amount = Attack_Split(game, attack, my)
            attack_potential = attack.custom_pp(amount) + SP(game, attack.target)
            if upgrade_PP > attack.potential:
                if Max_Send_Amount(game, my) > my.upgrade_cost and my not in ice_used:
                    my.upgrade()
                    #print('Upgraded_Ice:', my,'Upgrade_PP: ', upgrade_PP, "Attack_PP ", attack_potential)
                ice_used.add(my)
            else:
                break

        
    for attack in attack_infos:
        if attack.target in game.get_my_icebergs():
            print('Defence: ', attack)
        else:
            print('Attack: ', attack)

        if attack.can_execute > 0:
            for ice in attack.group:
                #print('ice:',ice,'!!!!!')
                ice_used.add(ice)
            continue #then dvir
            
        for ice in attack.group:
            #print('ice used:',ice_used)
            if ice in ice_used:
                break
        else:
            Attack(game, attack, ice_used)
