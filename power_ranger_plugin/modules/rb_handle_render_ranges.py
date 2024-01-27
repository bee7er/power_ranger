"""
Application:    Power Ranger Plugin
Copyright:      PowerHouse Industries Nov 2023
Author:         Brian Etheridge
"""

import c4d, time
from c4d import documents
from c4d import gui
import rb_functions

config = rb_functions.get_config_values()
debug = bool(int(config.get(rb_functions.CONFIG_SECTION, 'debug')))
verbose = bool(int(config.get(rb_functions.CONFIG_SECTION, 'verbose')))

# ===================================================================
def handle_render_takes(customFrameRangesAry):
# ===================================================================
    # Submits a render request for one or more frames to the BatchRender queue
    # ........................................................................

    newRenderArray = []
    newTakeArray = []
    takeData = None
    result = False
    try:
        if True == debug:
            print("*** In handle_render_queue")

        doc = documents.GetActiveDocument()

        # Gets the TakeData from the active document (holds all information about Takes)
        takeData = doc.GetTakeData()
        if takeData is None:
            raise RuntimeError("Failed to retrieve the take data")

        activeRenderData = doc.GetActiveRenderData()
        if activeRenderData is None:
            raise RuntimeError("Failed to retrieve the active render data")

        # Check to see if we have a save path defined
        if "" == activeRenderData[c4d.RDATA_PATH]:
            print("*** WARNING: No save path has been defined")

        for range in customFrameRangesAry:
            frameFrom = int(range[0])
            frameTo = int(range[1])
            if True == debug:
                print("*** Adding entry for range limit from: " + str(frameFrom) + " to " + str(frameTo))

            # Create new render data
            if True == verbose:
                print("*** Cloning render data")
            renderData = activeRenderData.GetClone()

            # Save the render for later housekeeping
            newRenderArray.append(renderData)

            # Set the chunk frame range in this instance of the project
            renderData[c4d.RDATA_FRAMEFROM] = c4d.BaseTime(frameFrom, renderData[c4d.RDATA_FRAMERATE])
            renderData[c4d.RDATA_FRAMETO] = c4d.BaseTime(frameTo, renderData[c4d.RDATA_FRAMERATE])

            doc.InsertRenderData(renderData, activeRenderData)

            # Creates a Take and defines the render data
            takeName = "Take for RenderData " + str(range)
            if True == debug:
                print("*** Adding Take: " + str(takeName))

            newTake = takeData.AddTake(takeName, None, None)
            if newTake is None:
                raise RuntimeError("Failed to create a new take")

            if True == debug:
                print("*** New take was added: " + takeName)
            newTake.SetRenderData(takeData, renderData)
            if True == debug:
                print("*** Marking take as selected")
            newTake.SetChecked(True)

            # Save the take for later housekeeping
            newTakeArray.append(newTake)

        if True == debug:
            print("*** Rendering Take: from " + str(renderData[c4d.RDATA_FRAMEFROM].Get()) + " to " + str(renderData[c4d.RDATA_FRAMETO].Get()))

        # Render Marked Takes to Picture Viewer
        c4d.CallCommand(431000068)  # ID_431000068

        if True == debug:
            print("*** Finished rendering selected takes")

        # Pushes an update event to Cinema 4D to force a redraw in the GUI
        c4d.EventAdd()

        result = True

    except Exception as e:
        message = "Error handling takes. Error message: " + str(e)
        print(message)
        gui.MessageDialog(message)

    # Housekeeping, remove the temporary render data and takes
    if True == debug:
        print("*** Housekeeping the removal of render data and takes")
    if 0 < len(newRenderArray):
        for render in newRenderArray:
            if True == debug:
                print("*** Deleting render")
            render.Remove()

    if 0 < len(newTakeArray) and takeData is not None:
        for take in newTakeArray:
            if True == debug:
                print("*** Deleting take")
            takeData.DeleteTake(take)

    return result
