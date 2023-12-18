"""
Application:    Power Ranger Plugin
Copyright:      PowerHouse Industries Nov 2023
Author:         Brian Etheridge
"""

import os, platform, c4d

try:
    # R2023
    import configparser as configurator
    print("*** Power Ranger plugin started")
except:
    # Prior to R2023
    import ConfigParser as configurator
    print("** Power Ranger plugin started")

__root__ = os.path.dirname(os.path.dirname(__file__))

RANGE_FROM = "RANGE_FROM"
RANGE_TO = "RANGE_TO"
RANGE_STEP = "RANGE_STEP"
FRAME_RATE = "FRAME_RATE"

CONFIG_SECTION = 'CONFIG'
CONFIG_RANGER_SECTION = 'RANGER'

# State table constants
ERROR = 'e'
EXIT = 'x'
END = '#'
MASK_SIGN = 'm'

CONFIG_FILE = __root__ + '/config/properties.ini'

# ===================================================================
def get_config_values():
# ===================================================================
    # Returns entries in the config file
    # .....................................................
    config = configurator.ConfigParser()
    # Replace the translate function with 'str', which will stop ini field names from being lower cased
    config.optionxform = str
    config.read(CONFIG_FILE)
      
    return config

# ===================================================================
def update_config_values(section, configFields):
# ===================================================================
    # Updates a list of tuples of config field name and values
    # .....................................................

    config = get_config_values()
    verbose = config.get(CONFIG_SECTION, 'verbose')
    
    # configfields is a list of tuples:
    #    [('field name', 'field value'), ('field name', 'field value'), ...]
    #
    for field in configFields:
        if True == verbose:
            print("Config out: ", field[0], field[1])
        config.set(section, field[0], field[1])

    with open(CONFIG_FILE, 'w') as configFile:
        config.write(configFile)
        
    return config 

# ===================================================================
def analyse_frame_ranges(frameRangeStr):
# ===================================================================
    # Analyses a string of frame ranges, validates them and returns a list of them
    # .....................................................
    config = get_config_values()
    verbose = config.get(CONFIG_SECTION, 'verbose')

    # Remove all spaces and plus signs, which are valid but not needed
    frameRangeLst = frameRangeStr.replace(' ', '').replace('+', '').split(',')

    # First of all, allow for negative numbers, although we cannot render negative frames
    frameRangeVldLst = []
    for entry in frameRangeLst:
        res = stateTransitionRangelet(entry)
        if False is not res:
            # Copy to output
            frameRangeVldLst.append(res)

    rangeArray = []

    for entry in frameRangeVldLst:
        # Range should be number-number
        rangelet = entry.split('-')
        if 1 == len(rangelet):
            # Build a rangelet from what we've been given, e.g. 12 -> 12-12
            rangelet = [rangelet[0], rangelet[0]]
        # Convert from masked signs, we cannot render negative frame numbers
        if 0 <= str(rangelet[0]).find(MASK_SIGN):
            rangelet[0] = 0
            print("*** WARNING: it is not possible to render negative frames for lower range limit")
        if 0 <= str(rangelet[1]).find(MASK_SIGN):
            rangelet[1] = 0
            print("*** WARNING: it is not possible to render negative frames for upper range limit")

        if True == verbose:
            print("Adjusted rangelet: ", rangelet)
        # Check what we've got
        if 2 < len(rangelet):
            if True == verbose:
                print("Error: Ignoring invalid rangelet: ", str(rangelet))
            continue
        elif True != isValidNumber(str(rangelet[0])) or True != isValidNumber(str(rangelet[1])):
            if True == verbose:
                print("Error: Ignoring non-integer rangelet: ", str(rangelet))
            continue
        elif int(rangelet[1]) < int(rangelet[0]):
            el = rangelet[0]
            rangelet[0] = rangelet[1]
            rangelet[1] = el
            
        rangeArray.append(rangelet)

    return normalise_frame_ranges(rangeArray)

# ===================================================================
def sortNumeric(val):
# ===================================================================
    # We sort on the first element of the array, but make sure it is
    # a numeric comparison so that 7 is before 15 (ie '7' > '15')
    return int(val[0])

# ===================================================================
def normalise_frame_ranges(rangeArray):
# ===================================================================
    # Check that the set of rangelets make sense
    # .....................................................
    outArray = []
    # If we have one or no ranges specified then nothing complicated to do here
    if 1 >= len(rangeArray):
        outArray = rangeArray

    else:
        # Do a numeric sort into ascending order
        rangeArray.sort(key=sortNumeric)
        for elem in rangeArray:
            outArrayLen = len(outArray)
            if 0 >= outArrayLen:
                outArray.append(elem)
                continue

            # If start of range is less than or equal to end of range plus 1
            # E.g. 1-1, 2-6, combine them as 1-6
            if int(elem[0]) <= int(outArray[outArrayLen - 1][1]) + 1:
                if int(elem[1]) >= int(outArray[outArrayLen - 1][1]):
                    outArray[outArrayLen - 1][1] = elem[1]
                # We have adjusted the out array and do not need the element
                continue

            # Just add this new rangelet to out array
            outArray.append(elem)

    returnStr = sep = ''
    for elem in outArray:
        returnStr += sep + str(elem[0]) + '-' + str(elem[1])
        sep = ','

    # Return both the string and array versions of the normalise data
    return returnStr, outArray

# ===================================================================
def isValidNumber(numberStr):
# ===================================================================
    if numberStr.isdigit():
        return True
    elif numberStr[0] == '-' and str(numberStr[1:]).isdigit():
        return True
    return False

# ===================================================================
def isDigit(char):
# ===================================================================
    if "0" <= char and "9" >= char:
        return True
    return False

# ===================================================================
def isMinus(char):
# ===================================================================
    if '-' == char:
        return True
    return False

# ===================================================================
def isAnotherChar(char):
# ===================================================================
    if isDigit(char):
        return False
    elif isMinus(char):
        return False
    elif isEnd(char):
        return False
    return True

# ===================================================================
def isEnd(char):
# ===================================================================
    if END == char:
        return True
    return False

# ===================================================================
def stateTransitionRangelet(rangelet):
# ===================================================================
    # We receive a range definition.   It can be in the form:
    #       -n-m
    #       -n--m
    #       n--m
    #       n-m
    # Each of these is acceptable, where n and m are any numeric value
    # We validate and reorganise the rangelet and return it, or blank if it is invalid
    # We use a state transition table to drive the validation process

    # Key:
    # a = any value
    # d = digit
    # e = error
    # n = end
    # x = exit
    # - = minus sign
    # The table consists of:
    #   state   test   goto state

    stateTable = [
        ['1','isDigit','2',''],
        ['1','isMinus','3',MASK_SIGN],
        ['1','isAnotherChar','e',''],
        ['1','isEnd','e',''],
        ['2','isDigit','2',''],
        ['2','isMinus','4',''],
        ['2','isAnotherChar','e',''],
        ['2','isEnd','x',''],
        ['3','isDigit','2',''],
        ['3','isMinus','e',''],
        ['3','isAnotherChar','e',''],
        ['3','isEnd','e',''],
        ['4','isDigit','5',''],
        ['4','isMinus','6',MASK_SIGN],
        ['4','isAnotherChar','e',''],
        ['4','isEnd','e',''],
        ['5','isDigit','5',''],
        ['5','isMinus','e',''],
        ['5','isAnotherChar','e',''],
        ['5','isEnd','x',''],
        ['6','isDigit','5',''],
        ['6','isMinus','e',''],
        ['6','isAnotherChar','e',''],
        ['6','isEnd','e',''],
        ]

    config = get_config_values()
    debug = config.get(CONFIG_SECTION, 'debug')
    rangelet += END     # Add a termination character to signal the end
    currentState = '1'  # Starting point
    returnRangelet = ''
    for char in rangelet:

        for stateElem in stateTable:

            if currentState == stateElem[0]:
                evalStr = stateElem[1] + '(' + "'" + char + "')"
                if True == eval(evalStr):
                    # Action can only be e=error, x=exit or the next state
                    if ERROR == stateElem[2]:
                        if True == debug:
                            print("*** Error detected. Ignoring rangelet: " + rangelet)
                        return False

                    elif EXIT == stateElem[2]:
                        if True == debug:
                            print("*** Exit detected. Rangelet " + rangelet + " passes validation.")
                        return returnRangelet

                    else:
                        # If it is minus sign we mask it because the '-' operator is used to separate the elements later
                        if MASK_SIGN == stateElem[3]:       # Only present if we just encountered '-'
                            returnRangelet += MASK_SIGN
                        else:
                            returnRangelet += char

                        currentState = stateElem[2]
                        # Next char
                        break

    return returnRangelet

# ===================================================================
def get_render_settings():
# ===================================================================
    # Gets render settings from the current active set
    # .....................................................

    activeDocument = c4d.documents.GetActiveDocument()
    renderData = activeDocument.GetActiveRenderData()

    return {
        RANGE_FROM: int(renderData[c4d.RDATA_FRAMEFROM].Get() * renderData[c4d.RDATA_FRAMERATE]),
        RANGE_TO: int(renderData[c4d.RDATA_FRAMETO].Get() * renderData[c4d.RDATA_FRAMERATE]),
        RANGE_STEP: renderData[c4d.RDATA_FRAMESTEP],
        FRAME_RATE: int(renderData[c4d.RDATA_FRAMERATE])
    }

# ===================================================================
def get_projectFullPath():
# ===================================================================
    # Gets project full path and name from the currently loaded project
    # .................................................................
    if '' == get_projectName():
        print("*** A project has not yet been opened")
        return ''

    md = c4d.documents.GetActiveDocument()
    path = c4d.documents.BaseDocument.GetDocumentPath(md)
    name = c4d.documents.BaseDocument.GetDocumentName(md)

    c4dProjectFullPath = os.path.join(path, c4d.documents.BaseDocument.GetDocumentName(md))

    return c4dProjectFullPath

# ===================================================================
def get_projectPath():
# ===================================================================
    # Gets project path from the currently loaded project
    # ...................................................
    if '' == get_projectName():
        print("*** A project has not yet been opened")
        return ''

    md = c4d.documents.GetActiveDocument()
    path = c4d.documents.BaseDocument.GetDocumentPath(md)

    return path

# ===================================================================
def get_projectName():
# ===================================================================
    # Gets project name from the currently loaded project
    # ...................................................

    md = c4d.documents.GetActiveDocument()

    projectName = c4d.documents.BaseDocument.GetDocumentName(md)
    if 0 <= projectName.find('Untitled'):
        print("*** A project has not yet been opened")
        return ''

    return projectName
