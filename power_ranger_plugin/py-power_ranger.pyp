"""
Application:    Power Ranger Plugin
Copyright:      PowerHouse Industries Nov 2023
Author:         Brian Etheridge

Description:
    A Cinema 4D plugin to assist with rendering individual or ranges of frames using the Takes system.
"""

import os, sys
import c4d
from c4d import gui, bitmaps, utils
from c4d import documents
from c4d import modules
# Add modules to the path before trying to reference them
__root__ = os.path.dirname(__file__)
if os.path.join(__root__, 'modules') not in sys.path: sys.path.insert(0, os.path.join(__root__, 'modules'))
# Ranger modules for various shared functions
import rb_functions, rb_handle_render_ranges

__res__ = c4d.plugins.GeResource()
__res__.Init(__root__)

# Unique ID obtained from www.plugincafe.com 20231214
PLUGIN_ID = 1062133
GROUP_ID_HELP = 100000
GROUP_ID_FORM = 100001

FRAME_RANGES_HELP_1 = 100012
FRAME_RANGES_HELP_2 = 100013
EDIT_FRAME_RANGES_TEXT = 100016
RENDER_BUTTON = 100017
GAPS_BUTTON = 100018
CLOSE_BUTTON = 100019
TAG_LINE = 100021

PATH = "RDATA_PATH"

config = rb_functions.get_config_values()
debug = bool(int(config.get(rb_functions.CONFIG_SECTION, 'debug')))
verbose = bool(int(config.get(rb_functions.CONFIG_SECTION, 'verbose')))

# ===================================================================
class RangerDlg(c4d.gui.GeDialog):
# ===================================================================

    customFrameRanges = config.get(rb_functions.CONFIG_RANGER_SECTION, 'customFrameRanges')
    customFrameRangesAry = []

    # ===================================================================
    def CreateLayout(self):
    # ===================================================================
        """ Called when Cinema 4D creates the dialog """

        self.SetTitle("Power Ranger")

        self.GroupBegin(id=GROUP_ID_HELP, flags=c4d.BFH_SCALEFIT, cols=1, rows=3)
        # Spaces: left, top, right, bottom
        self.GroupBorderSpace(10,10,10,10)
        """ Instructions """
        self.AddStaticText(id=FRAME_RANGES_HELP_1, flags=c4d.BFV_MASK, initw=385, name="Specify one or more frames or ranges of frames.", borderstyle=c4d.BORDER_NONE)
        self.AddStaticText(id=FRAME_RANGES_HELP_2, flags=c4d.BFV_MASK, initw=385, name="Example: 1,8,10-15,55", borderstyle=c4d.BORDER_NONE)
        self.GroupEnd()

        self.GroupBegin(id=GROUP_ID_HELP, flags=c4d.BFH_SCALEFIT, cols=1, rows=1)
        # Spaces: left, top, right, bottom
        self.GroupBorderSpace(10,0,10,0)
        """ Custom ranges field """
        self.AddEditText(id=EDIT_FRAME_RANGES_TEXT, flags=c4d.BFV_MASK, initw=440, inith=16, editflags=0)
        self.SetString(id=EDIT_FRAME_RANGES_TEXT, value=self.customFrameRanges)
        self.AddStaticText(id=TAG_LINE, flags=c4d.BFH_FIT | c4d.BFH_RIGHT, initw=440, name="Powerhouse Industries", borderstyle=c4d.BORDER_NONE)
        # self.AddStaticText(id=TAG_LINE, flags=c4d.BFH_RIGHT, initw=440, name="https://powerhouse.industries", borderstyle=c4d.BORDER_NONE)
        self.GroupEnd()

        self.GroupBegin(id=GROUP_ID_FORM, flags=c4d.BFH_SCALEFIT, cols=3, rows=5)
        # Spaces: left, top, right, bottom
        self.GroupBorderSpace(10,20,10,20)
        """ Button fields """
        self.AddButton(id=CLOSE_BUTTON, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=100, inith=16, name="Close")
        self.AddButton(id=GAPS_BUTTON, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=100, inith=16, name="Fill Those Gaps")
        self.AddButton(id=RENDER_BUTTON, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=100, inith=16, name="Render")
        self.GroupEnd()

        return True

    # ===================================================================
    def Command(self, messageId, bc):
    # ===================================================================
        """
        Called when the user clicks on the dialog or clicks a button
            messageId (int): The ID of the resource that triggered the event
            bc (c4d.BaseContainer): The original message container
        Returns False on error else True.
        """

        # User click on Ok button
        if messageId == RENDER_BUTTON:

            print("Rendering frames")
            if '' == rb_functions.get_projectName():
                gui.MessageDialog("Please open your project file")
                return True

            self.customFrameRanges = self.GetString(EDIT_FRAME_RANGES_TEXT)

            # Analyse the custom frame ranges
            self.customFrameRanges, self.customFrameRangesAry = rb_functions.analyse_frame_ranges(self.customFrameRanges)
            if '' == self.customFrameRanges:
                gui.MessageDialog("Please enter at least one valid range, in the format 'm - m, n - n, etc'")
                return False

            if True == debug:
                print("Custom frame ranges following analyses: " + self.customFrameRanges)

            if True == debug:
                print("Frame range(s): " + self.customFrameRanges)

            # Save changes to the config file
            rb_functions.update_config_values(rb_functions.CONFIG_RANGER_SECTION, [
                ('customFrameRanges', str(self.customFrameRanges))
                ])

            # Create entries in the render queue for the frame ranges entered
            if True == self.submitRangeDetails():
                # Update the dialog with the normalised frame ranges
                self.SetString(id=EDIT_FRAME_RANGES_TEXT, value=str(self.customFrameRanges))

                # Currently leaving the dialog open
                ######self.Close()

            else:
                if True == debug:
                    print("Render frame ranges cancelled")
                return False

            return True

        # User clicked on the Gaps button
        elif messageId == GAPS_BUTTON:

            print('Checking for gaps in the rendered image sequence')
            # Create entries in the render queue for gaps in the images in the output folder
            if True == self.calcImageGapDetails():
                # Update the dialog with the normalised frame ranges
                self.SetString(id=EDIT_FRAME_RANGES_TEXT, value=str(self.customFrameRanges))

            return True


        # User clicked on the Close button
        elif messageId == CLOSE_BUTTON:

            print("Dialog closed")
            # Close the Dialog
            self.Close()
            return True

        return True

    # ===================================================================
    def calcImageGapDetails(self):
    # ===================================================================
        '''
        Here we examine the contents of the output folder.
        Using the rendered file prefix we check the list of image files
        for any gaps in the sequence.  We return the sequence numbers of
        the gaps.
        '''

        renderData = rb_functions.get_render_settings()
        # Check to see if we have a save path defined
        outputPath = renderData[PATH]
        # Could default the path to os.sep, but for now we will reject it
        if "" == outputPath:
            gui.MessageDialog("No save path has been specified in project settings")
            return False

        # Remove the generic fileName prefix, which is the last element of the list of folders
        pathLst = outputPath.split(os.sep)
        lastElem = pathLst.pop()
        # Put the remaining path elements back into a string
        outputPath = os.sep.join(pathLst)
        # Get file contents from the output path
        filePrefix = lastElem
        if '$prj' == filePrefix:
            filePrefix = rb_functions.get_projectName()

        filePrefix = filePrefix.replace('.c4d', '')

        atLeastOne = False
        returnedSequenceNumbers = ''
        sep = ''

        directory = os.fsencode(outputPath)
        # Reduce the contents to a list of numeric suffixes
        seqLen = -1
        dirSequenceNumberList = []
        for file in os.listdir(directory):
            fileName = os.fsdecode(file)
            if fileName.startswith(filePrefix):
                # We must check that the entries are all the same length
                dirSequenceNumberElem = rb_functions.getFileSequenceNumber(filePrefix, fileName)
                newLen = len(dirSequenceNumberElem)
                if seqLen != -1 and newLen != seqLen:
                    gui.MessageDialog("Multiple sequence lengths: " + str(seqLen) + " and " + str(newLen) + "\nFolder cannot be processed.")
                    return False

                if False == dirSequenceNumberElem.isnumeric():
                    if True == debug:
                        # Ignore non-numeric elements
                        print("Ignoring non-numeric sequence '" + dirSequenceNumberElem + "'.")
                    continue

                seqLen = newLen
                dirSequenceNumberList.append(dirSequenceNumberElem)
                atLeastOne = True
                continue
            else:
                continue

        if False == atLeastOne:
            gui.MessageDialog(
                "There are no image files that match the file prefix '" +
                filePrefix +
                "'.\nIt is not possible process an empty output folder."
                )
            return False

        else:
            sequenceNumber = -1
            # Make sure our list of suffixes is sorted in ascending order
            dirSequenceNumberList.sort()

            # Make sure the list does not have duplicates
            lastElem = ''
            for dirSequenceNumberStr in dirSequenceNumberList:
                if lastElem == dirSequenceNumberStr:
                    if True == debug:
                        print("Removing duplicate sequence '" + dirSequenceNumberStr + "'.")
                    dirSequenceNumberList.remove(dirSequenceNumberStr)

                lastElem = dirSequenceNumberStr

            # Ok, looks like we have a list we can process
            seqLen = len(dirSequenceNumberList[0])

            for dirSequenceNumberStr in dirSequenceNumberList:
                sequenceNumber += 1
                testSequenceNumberStr = rb_functions.getTestSequenceNumber(sequenceNumber, seqLen)

                if testSequenceNumberStr != dirSequenceNumberStr:
                    while testSequenceNumberStr != dirSequenceNumberStr:
                        if True == debug:
                            print("Sequence number required: '" + testSequenceNumberStr + "'.")
                        returnedSequenceNumbers += (sep + str(int(testSequenceNumberStr)))
                        sep = ','

                        sequenceNumber += 1
                        testSequenceNumberStr = rb_functions.getTestSequenceNumber(sequenceNumber, seqLen)

        if '' == returnedSequenceNumbers:
            lastElem = dirSequenceNumberList.pop()
            gui.MessageDialog("There are no gaps.\nHighest sequence found was: " + lastElem)
            return False

        else:
            self.customFrameRanges, self.customFrameRangesAry = rb_functions.analyse_frame_ranges(returnedSequenceNumbers)

        return True

    # ===================================================================
    def submitRangeDetails(self):
    # ===================================================================
        # Get the user to confirm the submission
        yesNo = gui.QuestionDialog(
            "Submitting frames: \n" + self.customFrameRanges + "\n\n" +
            "Click Yes to continue.\n\n"
            )
        if False == yesNo:
            if True == debug:
                print("User cancelled the request")
            return False

        if True == rb_handle_render_ranges.handle_render_takes(self.customFrameRangesAry):
            if True == debug:
                print("Custom frame ranges added to takes and processed successfully")

        else:
            print("Unexpected result from processing custom frame ranges")
            return False

        return True

# ===================================================================
class RangerDlgCommand(c4d.plugins.CommandData):
# ===================================================================
    """
    Command Data class holding the RenderDlg instance
    """
    dialog = None

    # ===================================================================
    def Execute(self, doc):
    # ===================================================================
        """
        Called when the user executes CallCommand() or a menu option
        Returns True if the command success.
        """
        # Creates the dialog if it does not already exists
        if self.dialog is None:
            self.dialog = RangerDlg()

        # Opens the dialog
        return self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, pluginid=PLUGIN_ID, defaultw=400, defaulth=32)

    # ===================================================================
    def RestoreLayout(self, sec_ref):
    # ===================================================================
        """
        Restore an asynchronous dialog that has been displayed in the users layout
        Returns True if the restore successful
        """
        # Creates the dialog if its not already exists
        if self.dialog is None:
            self.dialog = RangerDlg()

        # Restores the layout
        return self.dialog.Restore(pluginid=PLUGIN_ID, secret=sec_ref)

# ===================================================================
# main entry function
# ===================================================================
if __name__ == "__main__":
    if True == verbose:
        print("Setting up Power Ranger Plugin")

    # Retrieves the icon path
    directory, _ = os.path.split(__file__)
    fn = os.path.join(directory, "res", "icon_ranger.tif")

    # Creates a BaseBitmap
    bbmp = c4d.bitmaps.BaseBitmap()
    if bbmp is None:
        raise MemoryError("Failed to create a BaseBitmap.")

    # Init the BaseBitmap with the icon
    if bbmp.InitWith(fn)[0] != c4d.IMAGERESULT_OK:
        raise MemoryError("Failed to initialise the BaseBitmap.")

    # Registers the plugin
    c4d.plugins.RegisterCommandPlugin(id=PLUGIN_ID,
                                      str="Power Ranger using the Take System",
                                      info=0,
                                      help="Power Ranger",
                                      dat=RangerDlgCommand(),
                                      icon=bbmp)

    if True == verbose:
        print("Power Ranger Plugin set up ok")
