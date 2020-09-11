import functools
import os
import random
import time
from piui import PiUi
import threading
import sys
import socket
import selectors
import types
import time
import queue

current_dir = os.path.dirname(os.path.abspath(__file__))
'''
TODO:
-make a second queue that tracks incoming messages from the lights for the piui interface
-work on piui interface
-make the piui control multiple lights (already implemented in the wifi part of the code but
multiple light functionality has to be implemented with piui)
'''
#######################################
sel = selectors.DefaultSelector()#ADDED FOR WIFI. the selector object keeping track of the incoming wifi messages
######################################################


#####THE MOSTLY ORIGINAL DEMO PIUI PROGRAM
########################################

#stores info about a light module for display on the screen
class lightModulePiUiInfo:
    def __init__(self, port):
        self.port = port
        self.displayTime = 0
        self.state = "OFF" #can be ON, OFF, TURNING_ON, TURNING_OFF if using the toggle system; can be ON, OFF, CHANGING_STATE if using the button light control system
        self.name = "deskLight" #an example of a light name

class DemoPiUi(object):

    def __init__(self, queuey, receiveQueuey):
        self.title = None
        self.txt = None
        self.img = None
        self.ui = PiUi(img_dir=os.path.join(current_dir, 'imgs'))
        self.src = "sunset.png"
        self.queuey = queuey #ADDED FOR WIFI - queue to hold the outgoing messages, connecting the piui and wifi program threads
        self.receiveQueuey = receiveQueuey
        self.piuiLightDict = {}#this dict will store the active lights' lightModulePiUiInfo; keys are the port numbers
        self.currentPage = None
        #self.titles = {} #this is a dictionary that is used by the toggle page to remember the title for each light; keys are the port numbers

    def page_static(self):
        self.page = self.ui.new_ui_page(title="Static Content", prev_text="Back",
            onprevclick=self.main_menu)
        self.page.add_textbox("Add a mobile UI to your Raspberry Pi project", "h1")
        self.page.add_element("hr")
        self.page.add_textbox("You can use any static HTML element " + 
            "in your UI and <b>regular</b> <i>HTML</i> <u>formatting</u>.", "p")
        self.page.add_element("hr")
        self.page.add_textbox("Your python code can update page contents at any time.", "p")
        update = self.page.add_textbox("Like this...", "h2")
        time.sleep(2)
        for a in range(1, 5):
            update.set_text(str(a))
            time.sleep(1)

    def page_buttons(self):
        self.page = self.ui.new_ui_page(title="Buttons", prev_text="Back", onprevclick=self.main_menu)
        self.title = self.page.add_textbox("Buttons!", "h1")
        plus = self.page.add_button("Up Button &uarr;", self.onupclick)
        minus = self.page.add_button("Down Button &darr;", self.ondownclick)

    def page_input(self):
        self.page = self.ui.new_ui_page(title="Input", prev_text="Back", onprevclick=self.main_menu)
        self.title = self.page.add_textbox("Input", "h1")
        self.txt = self.page.add_input("text", "Name")
        button = self.page.add_button("Say Hello", self.onhelloclick)

    def page_images(self):
        self.page = self.ui.new_ui_page(title="Images", prev_text="Back", onprevclick=self.main_menu)
        self.img = self.page.add_image("sunset.png")
        self.page.add_element('br')
        button = self.page.add_button("Change The Picture", self.onpicclick)

    #old version of the light list using toggles
    '''
    def page_toggles(self):
        self.currentPage = "page_toggles"
        self.page = self.ui.new_ui_page(title="Toggles", prev_text="Back", onprevclick=self.main_menu)
        self.list = self.page.add_list()
        self.titles = {} # A dictionary that stores the textboxes on the page
        #now create a function  to load all the titles in the current lightDict back into the toggles page
        for port in self.piuiLightDict:
            self.list.add_item("Light "+str(port), toggle=True, ontoggle=functools.partial(self.ontoggle, port))#technically should make the toggle start in the correct position
            self.titles[port] = self.page.add_textbox("Light "+str(port)+" "+self.piuiLightDict[port].state, "h2")

        #also deal with closing connection
        #also think about if the toggle is pressed while a function is in progress...perhaps use a queue
        #self.currentIndex = 0
        #self.indices = {}#dictionary where ports are keys and indices corresponding to the ports are the items

        #self.list.add_item("Light 1", toggle=True, ontoggle=functools.partial(self.ontoggle, 0, "light 1"))
        #self.titles += [self.page.add_textbox("Light 1 off", "h2")]
        #self.list2 = self.page.add_list()
        #self.list2.add_item("Light 2", toggle=True, ontoggle=functools.partial(self.ontoggle, 1, "light 2"))
        #self.titles += [self.page.add_textbox("Light 2 off", "h2")]

        #check if there is an incoming message in the receiveQueuey queue
        while True:
            incomingSignal = self.lightReceiveEvent()
            if incomingSignal is not None:
                print("HEREEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
                self.processSignal(incomingSignal)

    def processSignal(self, incomingSignal):
        signal = incomingSignal.split(":")[1]
        port = int(incomingSignal.split(":")[0])
        print("SIGNALLLLLLLLLLLLLL:"+signal)
        if signal == "CONNECTED":
            print("EYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")
            #NOTE ALSO ADD LIGHT MODULE INITIALIZATION NOTEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
            self.piuiLightDict[port] = lightModulePiUiInfo(port)#add a new light module to the piui light dictionary
            if self.currentPage == "page_toggles":
                self.list.add_item("Trigger Light "+str(port), toggle=True, ontoggle=functools.partial(self.ontoggle, port))
                self.titles[port] = self.page.add_textbox("Light "+str(port)+" off", "h2")
            #self.indices[str(port)] = self.currentIndex
            #self.currentIndex += 1
        elif signal == "ON" or signal=="CON_ON":
            self.piuiLightDict[port].state = "ON"
            if self.currentPage == "page_toggles":
                self.changeLightText(port, "ON")
        elif signal =="OFF" or signal == "CON_OFF":
            self.piuiLightDict[port].state = "OFF"
            if self.currentPage == "page_toggles":
                self.changeLightText(port, "OFF")
        elif signal=="CLOSED":
            print("CLOSINGGGGGGGGGGGGGGGGGGGGGGGGGGgg")
            self.piuiLightDict.pop(port,None)#if the light has become offline, take it out of the dictionary
            if self.currentPage == "page_toggles":
                self.page_toggles()#reset the page_toggles page if a light has been taken out of the list
    '''

    def page_lightController(self):
        self.currentPage = "page_lightController"#still need to test to make sure this actually sets the variable correctly when loading a page

        self.page = self.ui.new_ui_page(title="Light Control", prev_text="Back", onprevclick=self.main_menu)
        self.list = self.page.add_list()
        self.titles = {} # A dictionary that stores the textboxes on the page
        for port in self.piuiLightDict:
            self.titles[port] = self.page.add_textbox("Light "+str(port)+" "+self.piuiLightDict[port].state, "h2")
            self.page.add_button("Change State", functools.partial(self.onLightControlClick, port))

        while True:
            incomingSignal = self.lightReceiveEvent()
            if incomingSignal is not None:#if there is a message coming from the wifi, process it
                self.processSignal(incomingSignal)

    def processSignal(self, incomingSignal):
        signal = incomingSignal.split(":")[1]
        port = int(incomingSignal.split(":")[0])
        if signal == "CONNECTED":
            self.piuiLightDict[port] = lightModulePiUiInfo(port)#add a new light module to the piui light dictionary
            if self.currentPage == "page_lightController":
                self.titles[port] = self.page.add_textbox("Light "+str(port)+" "+self.piuiLightDict[port].state, "h2")
                self.page.add_button("Change State", functools.partial(self.onLightControlClick, port))
        elif signal == "ON" or signal=="CON_ON":
            self.piuiLightDict[port].state = "ON"
            if self.currentPage == "page_lightController":
                self.changeLightText(port, "ON")
        elif signal =="OFF" or signal == "CON_OFF":
            self.piuiLightDict[port].state = "OFF"
            if self.currentPage == "page_lightController":
                self.changeLightText(port, "OFF")
        elif signal=="CLOSED":
            self.piuiLightDict.pop(port,None)#if the light has become offline, take it out of the dictionary
            if self.currentPage == "page_lightController":
                self.page_lightController()#reset the page_toggles page if a light has been taken out of the list



    '''
    def page_console(self):
        con = self.ui.console(title="Console", prev_text="Back", onprevclick=self.main_menu)
        con.print_line("Hello Console!")
    '''
    def main_menu(self):
        self.currentPage = "main_menu"#SHOULD TEST IF THIS ACTUYALLY CHANGES WHEN GOING BACK TO MAIN<<<<<<<<<<<<<<<<<<<<
        self.page = self.ui.new_ui_page(title="PiUi")
        self.list = self.page.add_list()
        self.list.add_item("Static Content", chevron=True, onclick=self.page_static)
        self.list.add_item("Buttons", chevron=True, onclick=self.page_buttons)
        self.list.add_item("Input", chevron=True, onclick=self.page_input)
        self.list.add_item("Images", chevron=True, onclick=self.page_images)
        self.list.add_item("Light Control", chevron=True, onclick=self.page_lightController)
        #self.list.add_item("Console!", chevron=True, onclick=self.page_console)
        while True:
            incomingSignal = self.lightReceiveEvent()
            if incomingSignal is not None:
                self.processSignal(incomingSignal)


        self.ui.done()

    def main(self):
        self.main_menu()
        self.ui.done()
        print("THREE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    def onupclick(self):
        self.title.set_text("Up ")
        #self.queuey.put("yo")#THIS LINE IS AN EXAMPLE OF SENDING A MESSAGE TO THE WIFI THREAD OF THE PROGRAM###########
        print ("Up")

    def ondownclick(self):
        self.title.set_text("Down")
        print ("Down")

    def onhelloclick(self):
        print ("onstartclick")
        self.title.set_text("Hello " + self.txt.get_text())
        print ("Start")

    def onpicclick(self):
        if self.src == "sunset.png":
          self.img.set_src("sunset2.png")
          self.src = "sunset2.png"
        else:
          self.img.set_src("sunset.png")
          self.src = "sunset.png"

    def onLightControlClick(self, port):
        value = "CHANGESTATE_COMMAND"
        self.piuiLightDict[port].state = "CHANGING_STATE"
        self.lightCommandEvent(str(port)+":"+value)
        self.changeLightText(port, "UNKNOWN")


    def ontoggle(self, port, value):#not being used right now
        if value == "TRUE":
            value = "ON_COMMAND"
            self.piuiLightDict[port].state = "TURNING_ON"
        else:
            value = "OFF_COMMAND"
            self.piuiLightDict[port].state = "TURNING_OFF"
        self.lightCommandEvent(str(port)+":"+value)
        self.changeLightText(port, "UNKNOWN")

    def changeLightText(self, port, text):
        #index = self.indices[str(port)]
        self.titles[port].set_text("Light "+str(port)+" " + text)

#AN EXAMPLE OF A POTENTIAL FUNCTION THAT COULD BE USED FOR
#SENDING WIFI MESSAGES FROM PIUI################
    def lightCommandEvent(self, command):
        self.queuey.put(command)

    def lightReceiveEvent(self):
        if not self.receiveQueuey.empty():
            return self.receiveQueuey.get()
        else:
            return None

##########################################



#############ADDED FOR WIFI - THE WIFI FUNCTIONS
#######################################
class lightModule:#CLASS THAT KEEPS TRACK OF THE STATUS OF A LIGHT AT A CERTAIN WIFI PORT
    def __init__(self, port):
        self.state = "OFF" #can be "OFF", "ON", "TURNING OFF", "TURNING ON"
        self.port = port#MUST FIX SO THAT IT STARTS AT THE CORRECT STATE
        self.changeTime = 0
        print("    Light ", self.port, " is now ONLINE.")

   #EDGE CASES TO FIX:
   #trying to turn light on or off while it is in unknown state
   #time.time goes past the max value and goes back to zero
   #address already in use when starting up piui

   #IMPORTANT ADDITIONS
   #add in the name changing commands
   #if the statenotchanged command keeps coming back confirm the correct state is being asked for, ie so that there is not an infinite loop because it is trying to turn on when the light is already on

   #OTHER IMPROVEMENTS:
   #instead of change state make it more precise control... ie option to turn on/off

    def changeState(self):
        if self.state == "OFF":
            #self.state = 1
            self.state = "TURNING ON"
            print("    Light ", self.port, " is now TURNING ON.")
        elif self.state == "ON":
            #self.state = 0
            self.state = "TURNING OFF"
            print("    Light ", self.port, " is now TURNING OFF.")
        self.changeTime = time.time()

    def confirmStateChange(self):#if no reply was received from the module for the original on/off command, then try sending command again
        self.changeTime = time.time()#reset the time at which the state change was last attempted
        if self.state == "TURNING ON":
            print("    Light ", self.port, "turning on confirmation requested.")
        elif self.state == "TURNING OFF":
            print("    Light ", self.port, "turning off confirmation requested.")

    def finalizeStateChange(self):
        if self.state == "TURNING ON":
            #self.state = 1
            self.state = "ON"
            print("    Light ", self.port, " is now ON.")
        elif self.state == "TURNING OFF":
            #self.state = 0
            self.state = "OFF"
            print("    Light ", self.port, " is now OFF.")

    def outOfSyncStateChange(self, forcedState):
        if forcedState == "ON":
            self.state = "ON"
            print("    Light ", self.port, " is now FORCED ON, light module and piui were temporarily out of sync.")
        elif forcedState == "OFF":
            self.state = "OFF"
            print("    Light ", self.port, " is now FORCED OFF, light module and piui were temporarily out of sync.")

    def closeLight(self):
        print("    Light ", self.port, "is now OFFLINE.")

#FUNCTION TO CONNECT TO A NEW LIGHT MODULE AND ADD A LIGHTMODULE CLASS TO THE LIGHTMODULEDICT FOR THAT CONNECTION
def accept_wrapper(sock, lightModuleDict, receiveQueuey):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", messages=[b"CONNECTED"], outb=b"")#send a message to the light to confirm it has been connected
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    lightModuleDict[addr[1]] = lightModule(addr[1])
    print("CONNECTEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
    receiveQueuey.put(str(addr[1]) + ":" + "CONNECTED")

#SERVICE ANY INCOMING AND OUTGOING WIFI COMMANDS FOR A GIVEN LIGHT MODULE
def service_connection(key, mask, lightModuleDict, changeState, receiveQueuey, changePort):
    sock = key.fileobj
    data = key.data
    port = data.addr[1]
    lightModule = lightModuleDict[port]#the port of the currently serviced light module is data.addr[1]
    if changeState == True and changePort == int(port): #if a state change has been for the current port by the queue
        data.messages  += [b"CHANGE STATE"]
        lightModule.changeState()

    #check if any messages have been received from the light module
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)  # Should be ready to read
        except:
            recv_data = False#if read failed then close light
        if recv_data:
            print("received",repr(recv_data), "from", data.addr)
           #IT WOULD ACTUALLY STILL BE GOOD TO HAVE AN IMMEDIATE CHECK OF CONFIRM STATE RIGHT AFTER THE LIGHT HAS BEEN CHANGED
            '''
            if recv_data == b"TURNED ON":#confirmation that the light has turned on/off
                lightModule.finalizeChangeState()
                receiveQueuey.put(str(port) + ":" + "ON")
                #data.outb += recv_data
            elif recv_data == b"TURNED OFF":
                lightModule.finalizeChangeState()
                receiveQueuey.put(str(port) + ":" + "OFF")
            if recv_data == b"CONFIRMED ON":#confirmation that the light has turned on/off after a delayed response
                lightModule.finalizeChangeState()
                receiveQueuey.put(str(port) + ":" + "CON_ON")
            elif recv_data == b"CONFIRMED OFF":
                lightModule.finalizeChangeState()
                receiveQueuey.put(str(port) + ":" + "CON_OFF")
            '''
            if recv_data == b"STATECHANGED_ON":
                if lightModule.state == "TURNING ON":#if the piui thinks that the light is actually supposed to be turning on
                    lightModule.finalizeStateChange()#FINISH ADDING ALL THE POSSIBILITIES HEREEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
                elif lightModule.state == "TURNING OFF":
                    lightModule.outOfSyncStateChange("ON")
                receiveQueuey.put(str(port) + ":" + "ON")
            elif recv_data == b"STATECHANGED_OFF":
                if lightModule.state == "TURNING OFF":#if the piui thinks that the light is actually supposed to be turning off
                    lightModule.finalizeStateChange()#FINISH ADDING ALL THE POSSIBILITIES HEREEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
                elif lightModule.state == "TURNING ON":
                    lightModule.outOfSyncStateChange("OFF")
                receiveQueuey.put(str(port) + ":" + "OFF")
            elif recv_data[0:15] == b"STATENOTCHANGED":
                #if the current light responded saying it has not yet changed state, confirm status again
                data.messages += [b"CONFIRM STATE"]
                lightModule.confirmStateChange()


        else:
            lightModule.closeLight()
            lightModuleDict.pop(port)
            print("closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()
            receiveQueuey.put(str(port) + ":" + "CLOSED")

    #if the current light has passed 2 seconds since attempting to turn on/off without response, confirm status
    if not data.messages: #must check to make sure the light was not just turned on or off
        if lightModule.state == "TURNING ON" and (time.time() - lightModule.changeTime) > 2:
            data.messages += [b"CONFIRM STATE"]
            lightModule.confirmStateChange()
        elif lightModule.state == "TURNING OFF" and (time.time() - lightModule.changeTime) > 2:
            data.messages += [b"CONFIRM STATE"]
            lightModule.confirmStateChange()

    #send any waiting messages to the light module
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop()
        if data.outb:
            print("Sending", repr(data.outb), "to", data.addr)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]
################################
#################################

def main(queuey, receiveQueuey):#####FROM ORIGINAL PIUI DEMO BUT ADDED THE WIFI MESSAGE QUEUE AS A PARAMETER
    piui = DemoPiUi(queuey, receiveQueuey)
    piui.main()


####CODE BELOW ADDED FOR WIFI
########THIS FUNCTION IS THE THREAD THAT CONTROLS THE WIFI CONNECTIONS
def side_Thread(queuey, receiveQueuey):
    host = "192.168.4.1"
    port = 50007
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    print("listening on", (host, port))
    lsock.setblocking(False)

    sel.register(lsock, selectors.EVENT_READ, data=None)


    try:
        lightModuleDict = {}
        changeState = False
        startTime = time.time()
        latestMessage = None
        changePort = None
        while True:
            #check the queue for all on/off events here
            #consumer
            #while not pipeline.empty():
            #    message = pipeline.get_message()
            #    add message to list/queue of commands to pursue

            #old time based switching
            #if time.time() - startTime > 7:
            #    changeState = True
            #    startTime = time.time()

            #simple test to see if queue messaging system works
            if not queuey.empty():#right now whenever there is a message the light state is changed; in the future there can be other messages such as asking for the light name
                latestMessage = queuey.get()
                changeState = True
                changePort = int(latestMessage.split(":")[0])#the port to be toggled is stored in the message before the colon

            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj, lightModuleDict, receiveQueuey)
                else:
                    service_connection(key, mask, lightModuleDict, changeState, receiveQueuey, changePort)
            changeState = False
            changePort = None
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        sel.close()
#################################
###############################

##THIS RUNS WHEN THE PROGRAM RUNS
if __name__ == '__main__':
    if len(sys.argv) != 1:
        print("usage:", sys.argv[0], "no input arguments")
        sys.exit(1)
    queuey = queue.Queue(maxsize=10)#the wifi and piui threads communicate using this queue
    receiveQueuey  = queue.Queue(maxsize=10)
    #the queue stores messages that the piui program wants to send until the wifi program is ready to send them
    #another queue should be created for incoming light status messages
    x = threading.Thread(target=main, args=(queuey, receiveQueuey,))#START THE PIUI PROGRAM THREAD
    x.start()
    y = threading.Thread(target=side_Thread, args=(queuey, receiveQueuey,))#START THE WIFI PROGRAM THREAD
    y.start()


