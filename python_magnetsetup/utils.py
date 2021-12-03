def Merge(dict1, dict2):
    """
    Merge dict1 and dict2 to form a new dictionnary
    """

    res = {**dict1, **dict2}
    return res    

def NMerge(dict1: dict, dict2: dict, debug: bool=False) -> dict:
    for key in dict1:
        if key in dict2:
            if debug:
                print("%s already in res" % key, type(dict1[key]))
            if isinstance(dict1[key], list):
                for item in dict1[key]:
                    if not item in dict2[key]:
                        dict2[key].append(item)          

        else:
            dict2[key] = dict1[key]
    
    return dict2


