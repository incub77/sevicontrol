from modes import Modes


class Commands:
    TREE = {
        "ON": [
            "0000020002", 
            "402111017100", 
            "002112013301", 
            "602110017828",  
            "202110012d3d",  
            "702110016828",  
            "302110013d3d"  
        ],
        "OFF": [
            "0000050005" 
        ],
        "W": {
            "1": {
                "FWD": [
                    "602110017828",  
                    "202110012d3d",  
                    "702110016828",  
                    "302110013d3d"  
                ],
                "REV": [
                    "602110016d3d",  
                    "202110013828",  
                    "702110017d3d",  
                    "302110012828"  
                ]
            },
            "2": {
                "FWD": [
                    "602110014a1a", 
                    "202110015a4a", 
                    "702110015a1a", 
                    "302110014a4a" 
                ],
                "REV": [
                    "602110011a4a", 
                    "202110010a1a", 
                    "702110010a4a", 
                    "302110011a1a" 
                ]
            },
            "3": {
                "FWD": [
                    "602110010151", 
                    "202110010313", 
                    "702110011151",  # Terasse, Schlafzimmer, DG
                    "302110011313"   # Wohnzimmer seite, Kinderzimmer, Spielzimmer
                ],
                "REV": [
                    "602110014313", 
                    "202110014151", 
                    "702110015313", 
                    "302110015151" 
                ]
            },
            "4": {
                "FWD": [
                    "602110015c0c", 
                    "202110017464", 
                    "702110014c0c",  # Terasse, Schlafzimmer, DG
                    "302110016464"   # Wohnzimmer seite, Kinderzimmer, Spielzimmer
                ],
                "REV": [
                    "602110013464", 
                    "202110011c0c",
                    "702110012464",
                    "302110010c0c",
                ]
            }
        },
        "S": {  # s-modes still 8-bit...
            "1": {
                "FWD": [
                    "602110017828",
                    "202110012d3d",
                    "3c211001313d",
                    "382110012028"
                ],
                "REV": [
                    "602110016d3d",
                    "202110013828",
                    "3c211001313d",
                    "382110012028"
                ]
            },
            "2": {
                "FWD": [
                    "602110011a4a",
                    "202110010a1a",
                    "3c211001464a",
                    "38211001121a"
                ],
                "REV": [
                    "602110014a1a",
                    "202110015a4a",
                    "3c211001464a",
                    "38211001121a"
                ]
            },
            "3": {
                "FWD": [
                    "602110014313",
                    "202110014151",
                    "3c2110015d51",
                    "382110011b13",
                ],
                "REV": [
                    "602110010151",
                    "202110010313",
                    "3c2110015d51",
                    "382110011b13"
                ]
            },
            "4": {
                "FWD": [
                    "602110015c0c",
                    "202110017464",
                    "3c2110016864",  # Terasse, Schlafzimmer, DG
                    "38211001040c"   # Wohnzimmer seite, Kinderzimmer, Spielzimmer
                ],
                "REV": [
                    "602110013464",
                    "202110011c0c",
                    "3c2110016864",
                    "38211001040c"
                ]
            }
        },
        "RECURRING": [
            "0012440056", 
            "0135500064", 
            "0033500063", 
            "0034500064" 
        ]
    }

    BY_MODE = {
        Modes.ON: TREE['ON'],
        Modes.OFF: TREE['OFF'],
        Modes.W1: TREE['W']['1'],
        Modes.W2: TREE['W']['2'],
        Modes.W3: TREE['W']['3'],
        Modes.W4: TREE['W']['4'],
        Modes.S1: TREE['S']['1'],
        Modes.S2: TREE['S']['2'],
        Modes.S3: TREE['S']['3'],
        Modes.S4: TREE['S']['4']
    }

    ON = TREE['ON']
    OFF = TREE['OFF']
    
    W1 = TREE['W']['1']['FWD']
    W1_REV = TREE['W']['1']['REV']
    W2 = TREE['W']['2']['FWD']
    W2_REV = TREE['W']['2']['REV']
    W3 = TREE['W']['3']['FWD']
    W3_REV = TREE['W']['3']['REV']
    W4 = TREE['W']['4']['FWD']
    W4_REV = TREE['W']['4']['REV']
    
    S1 = TREE['S']['1']['FWD']
    S1_REV = TREE['S']['1']['REV']
    S2 = TREE['S']['2']['FWD']
    S2_REV = TREE['S']['2']['REV']
    S3 = TREE['S']['3']['FWD']
    S3_REV = TREE['S']['3']['REV']
    S4 = TREE['S']['4']['FWD']
    S4_REV = TREE['S']['4']['REV']
    
    RECURRING = TREE['RECURRING']

    @staticmethod
    def extract_lists_from_dict(d):
        for key, value in d.items():
            if type(value) == list:
                yield value
            elif type(value) == dict:
                for l in Commands.extract_lists_from_dict(value):
                    yield l

    @staticmethod
    def generate_set_of_all_cmds():
        ret = set()
        for l in Commands.extract_lists_from_dict(Commands.TREE):
            for el in l:
                ret.add(el)
        return ret

