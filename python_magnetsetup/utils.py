def Merge(dict1, dict2):
    """
    Merge dict1 and dict2 to form a new dictionnary
    """

    res = {**dict1, **dict2}
    return res    

def NMerge(dict1: dict, dict2: dict, debug: bool=False, name: str="") -> dict:
    for key in dict1:
        if not dict2:
            dict2[key] = dict1[key]           
        else:
            if key in dict2:
                if debug:
                    print(f"{key} already in res")
                    print(f"NMerge({name}): dict1 {type(dict1[key])} dict2 {type(dict2[key])} objects key={key}")
                    print(f"dict1={dict1[key]}")
                    print(f"dict2={dict2[key]}")
                if type(dict1[key]) != type(dict2[key]):
                    raise Exception(f"NMerge: expect to have same type for key={key} in dict1 ({type(dict1[key])}) and in dict2 ({type(dict2[key])})")
                if isinstance(dict1[key], list):
                    for item in dict1[key]:
                        if not item in dict2[key]:
                            if debug: print(f"{item} not in dict2")
                            dict2[key].append(item)
                        # else:
                        #    print(f"{item} type={type(item)}")
                        #    print(f"dict1 item={item}")
                        #    index = dict2[key].index(item)
                        #    print(f"dict2 item={dict2[key][index]}")
                
                if debug:
                    print(f"NMerge({name}): result={dict2[key]}")         
            else:
                dict2[key] = dict1[key]
    
    return dict2


