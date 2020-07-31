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

sel = selectors.DefaultSelector()



class DemoPiUi(object):

    def __init__(self, pipeline):
        self.title = None
        self.txt = None
        self.img = None
        self.ui = PiUi(img_dir=os.path.join(current_dir, 'imgs'))
        self.src = "sunset.png"
        self.pipeline = pipeline #the event signalling a light status change

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
        self.list.add_item("Lights", chevron=False, toggle=True, ontoggle=functools.partial(self.ontoggle, "lights"))
        self.list.add_item("TV", chevron=False, toggle=True, ontoggle=functools.partial(self.ontoggle, "tv"))
        self.list.add_item("Microwave", chevron=False, toggle=True, ontoggle=functools.partial(self.ontoggle, "microwave"))
        self.page.add_element("hr")
        self.title = self.page.add_textbox("Home Appliance Control", "h1")
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

    def onupclick(self):
        self.title.set_text("Up ")
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

    def ontoggle(self, what, value):
        self.title.set_text("Toggled " + what + " " + str(value))

    def lightCommandEvent(self, command):
        self.pipeline.set_message(message, "Producer")


class Pipeline(queue.Queue):
    def __init__(self):
        super().__init__(maxsize=10)
    
    def get_message(self, name):
        value = self.get()
        return value
    
    def set_message(self, vale, name):
        self.put(value)


class lightModule:
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

    def confirmStateChange(self):
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

def accept_wrapper(sock, lightModuleDict):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", messages=[], outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    lightModuleDict[addr[1]] = lightModule(addr[1])


def service_connection(key, mask, lightModuleDict, changeState):
    sock = key.fileobj
    data = key.data
    lightModule = lightModuleDict[data.addr[1]]
    if changeState == True: #really sketch. Just demonstrating ideas
        data.messages  += [b"CHANGE STATE"]
        lightModule.changeState()

    #check if any messages have been received from the light module
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            print("received",repr(recv_data), "from", data.addr)
            if recv_data == b"TURNED ON" or recv_data == b"TURNED OFF":#confirmation that the light has turned on/off
                lightModule.finalizeChangeState()
                #data.outb += recv_data
            if recv_data == b"CONFIRMED ON" or recv_data == b"CONFIRMED OFF":#confirmation that the light has turned on/off after a delayed response
                lightModule.finalizeChangeState()
        else:
            lightModule.closeLight()
            lightModuleDict.pop(data.addr[1])
            print("closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()

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

def main(pipeline):
    piui = DemoPiUi(pipeline)
    piui.main()

def side_Thread(pipeline):
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
        lightCommandDatabase = []
        while True:
            #check the queue for all on/off events here
            #consumer
            #while not pipeline.empty():
            #    message = pipeline.get_message()
            #    add message to list of commands to pursue
            if time.time() - startTime > 7:
                changeState = True
                startTime = time.time()
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj, lightModuleDict)
                else:
                    service_connection(key, mask, lightModuleDict, changeState)
            changeState = False
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        sel.close()


if __name__ == '__main__':
    if len(sys.argv) != 1:
        print("usage:", sys.argv[0], "no input arguments")
        sys.exit(1)

    x = threading.Thread(target=main, args=())
    x.start()
    y = threading.Thread(target=side_Thread, args=())
    y.start()



