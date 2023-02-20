import itertools

def Merge(dict1, dict2):
    """
    Merge dict1 and dict2 to form a new dictionnary
    """

    res = {**dict1, **dict2}
    return res    

def NMerge(dict1: dict, dict2: dict, debug: bool=False, name: str="") -> dict:
    """
    concat ditc1 into dict2
    """

    if debug:
        print(f'NMerge({name}):')
        print(f'dict1: {dict1}')
        print(f'dict2: {dict2}')
    for key in dict1:
        if debug: 
            print(f'key={key}')
        if not dict2:
            if debug:
                print(f'create dict2 with {key} entry')
            dict2[key] = dict1[key]           
        else:
            if key in dict2:
                if debug:
                    print(f"{key} already in dict2")
                    print(f"dict1[{key}]={dict1[key]}")
                    print(f"dict2[{key}]={dict2[key]}")
                if type(dict1[key]) != type(dict2[key]):
                    raise Exception(f"NMerge: expect to have same type for key={key} in dict1 ({type(dict1[key])}) and in dict2 ({type(dict2[key])})")
                else:
                    if debug:
                        print(f"dict2[{key}] is {type(dict2[key])}")
                if isinstance(dict1[key], list):
                    for item in dict1[key]:
                        if not item in dict2[key]:
                            if debug:
                                print(f"{item} not in dict2 (type={type(item)})")
                            dict2[key].append(item)
                            if debug:
                                print(f"new dict2[{key}]={dict2[key]}")
                        else:
                            if debug:
                                #print(f"{item} type={type(item)}")
                                print(f"dict1[{key}] item={item}")
                                index = dict2[key].index(item)
                                print(f"dict2[{key}] item={dict2[key][index]}")
                    

                    if debug:
                        print(f"NMerge({name}): result dict2[{key}]={dict2[key]}")
                        if 'init_temp' in dict2:
                            print(f"NMerge({name}): dict2[init_temp]={dict2['init_temp']}")         
                        if 'power_magnet' in dict2:
                            print(f"NMerge({name}): dict2[power_magnet]={dict2['power_magnet']}")         
            else:
                if debug:
                    print(f'add {key} to dict2')
                dict2[key] = dict1[key]
    
    if debug:
        print(f'NMerge({name}): dict2: {dict2}')
    return 0


