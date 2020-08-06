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
class DemoPiUi(object):

    def __init__(self, queuey, receiveQueuey):
        self.title = None
        self.txt = None
        self.img = None
        self.ui = PiUi(img_dir=os.path.join(current_dir, 'imgs'))
        self.src = "sunset.png"
        self.queuey = queuey #ADDED FOR WIFI - queue to hold the outgoing messages, connecting the piui and wifi program threads
        self.receiveQueuey = receiveQueuey

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

    def page_toggles(self):
        self.page = self.ui.new_ui_page(title="Toggles", prev_text="Back", onprevclick=self.main_menu)
        self.list = self.page.add_list()
        self.titles = []
        self.currentIndex = 0
        self.indices = {}#dictionary where ports are keys and indices corresponding to the ports are the items
        '''
        self.list.add_item("Light 1", toggle=True, ontoggle=functools.partial(self.ontoggle, 0, "light 1"))
        self.titles += [self.page.add_textbox("Light 1 off", "h2")]
        self.list2 = self.page.add_list()
        self.list2.add_item("Light 2", toggle=True, ontoggle=functools.partial(self.ontoggle, 1, "light 2"))
        self.titles += [self.page.add_textbox("Light 2 off", "h2")]
        '''
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
            self.list.add_item("Light "+str(port), toggle=True, ontoggle=functools.partial(self.ontoggle, port))
            self.titles += [self.page.add_textbox("Light "+str(port)+" off", "h2")]
            self.indices[str(port)] = self.currentIndex
            self.currentIndex += 1
        elif signal == "ON" or signal=="CON_ON":
            self.changeLightText(port, "ON")
        elif signal =="OFF" or signal == "CON_OFF":
            self.changeLightText(port, "OFF")

    '''
    def page_console(self):
        con = self.ui.console(title="Console", prev_text="Back", onprevclick=self.main_menu)
        con.print_line("Hello Console!")
    '''
    def main_menu(self):
        self.page = self.ui.new_ui_page(title="PiUi")
        self.list = self.page.add_list()
        self.list.add_item("Static Content", chevron=True, onclick=self.page_static)
        self.list.add_item("Buttons", chevron=True, onclick=self.page_buttons)
        self.list.add_item("Input", chevron=True, onclick=self.page_input)
        self.list.add_item("Images", chevron=True, onclick=self.page_images)
        self.list.add_item("Toggles", chevron=True, onclick=self.page_toggles)
        #self.list.add_item("Console!", chevron=True, onclick=self.page_console)


        self.ui.done()

    def main(self):
        self.main_menu()
        self.ui.done()
        print("THREE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    def onupclick(self):
        self.title.set_text("Up ")
        self.queuey.put("yo")#THIS LINE IS AN EXAMPLE OF SENDING A MESSAGE TO THE WIFI THREAD OF THE PROGRAM###########
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

    def ontoggle(self, port, value):
        if value == "TRUE":
            value = "ON_COMMAND"
        else:
            value = "OFF_COMMAND"
        self.lightCommandEvent(str(port)+":"+value)

    def changeLightText(self, port, text):
        index = self.indices[str(port)]
        self.titles[index].set_text("Light "+str(port)+" " + text, "h2")

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
        self.state = 0 #0 is off, 1 is on, 2 is turning off, 3 is turning on
        self.port = port
        self.changeTime = 0
        print("    Light ", self.port, " is now ONLINE.")

   #EDGE CASES TO TAKE CARE OF:
   #trying to turn light on or off while it is in unknown state
   #time.time goes past the max value and goes back to zero
   #OTHER FIXES:
   #instead of change state make it more precise control... ie option to turn on/off

    def changeState(self):#must add "turning on/off" states
        if self.state == 0:
            #self.state = 1
            self.state = 3
            print("    Light ", self.port, " is now TURNING ON.")
        elif self.state == 1:
            #self.state = 0
            self.state = 2
            print("    Light ", self.port, " is now TURNING OFF.")
        self.changeTime = time.time()

    def confirmStateChange(self):#if no reply was received from the module for the original on/off command, then try again
        self.changeTime = time.time()#reset the time at which the state change was last attempted
        if self.state == 3:
            print("    Light ", self.port, "turning on confirmation requested.")
        elif self.state == 2:
            print("    Light ", self.port, "turning off confirmation requested.")

    def finalizeChangeState(self):
        if self.state == 3:
            #self.state = 1
            self.state = 1
            print("    Light ", self.port, " is now ON.")
        elif self.state == 2:
            #self.state = 0
            self.state = 0
            print("    Light ", self.port, " is now OFF.")

    def closeLight(self):
        print("    Light ", self.port, "is now OFFLINE.")

#FUNCTION TO CONNECT TO A NEW LIGHT MODULE AND ADD A LIGHTMODULE CLASS TO THE LIGHTMODULEDICT FOR THAT CONNECTION
def accept_wrapper(sock, lightModuleDict, receiveQueuey):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", messages=[], outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    lightModuleDict[addr[1]] = lightModule(addr[1])
    print("CONNECTEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
    receiveQueuey.put(str(addr[1]) + ":" + "CONNECTED")

#SERVICE ANY INCOMING AND OUTGOING WIFI COMMANDS FOR A GIVEN LIGHT MODULE
def service_connection(key, mask, lightModuleDict, changeState, receiveQueuey, changePort):
    sock = key.fileobj
    data = key.data
    lightModule = lightModuleDict[data.addr[1]]
    if changeState == True and changePort == int(data.addr[1]): #if a state change has been for the current port by the queue
        data.messages  += [b"CHANGE STATE"]
        lightModule.changeState()

    #check if any messages have been received from the light module
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            print("received",repr(recv_data), "from", data.addr)
            if recv_data == b"TURNED ON":#confirmation that the light has turned on/off
                lightModule.finalizeChangeState()
                receiveQueuey.put(str(data.addr[1]) + ":" + "ON")
                #data.outb += recv_data
            elif recv_data == b"TURNED OFF":
                lightModule.finalizeChangeState()
                receiveQueuey.put(str(data.addr[1]) + ":" + "OFF")
            if recv_data == b"CONFIRMED ON":#confirmation that the light has turned on/off after a delayed response
                lightModule.finalizeChangeState()
                receiveQueuey.put(str(data.addr[1]) + ":" + "CON_ON")
            elif recv_data == b"CONFIRMED OFF":
                lightModule.finalizeChangeState()
                receiveQueuey.put(str(data.addr[1]) + ":" + "CON_OFF")
        else:
            lightModule.closeLight()
            lightModuleDict.pop(data.addr[1])
            print("closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()
            receiveQueuey.put(str(data.addr[1]) + ":" + "CLOSED")

    #if the current light has passed 2 seconds since attempting to turn on/off without response, confirm status
    if not data.messages: #must check to make sure the light was not just turned on or off
        if lightModule.state == 3 and (time.time() - lightModule.changeTime) > 2:
            data.messages += [b"CONFIRM ON"]
            lightModule.confirmStateChange()
        elif lightModule.state == 2 and (time.time() - lightModule.changeTime) > 2:
            data.messages += [b"CONFIRM OFF"]
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
            if not queuey.empty():
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


