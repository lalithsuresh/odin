import gobject
import goocanvas
import gtk
import urllib2
import json
import time
import threading
import rsvg

MASTER_IP = "172.17.1.85"
MASTER_REST_PORT = "8080"
CLIENT_RESOURCE = "/odin/clients/connected/json"
AGENT_RESOURCE = "/odin/agents/json"
SPACING = 10
CANVAS_WIDTH = 1000

master = None
agent_item_map = {}
client_item_map =  {}



class CustomSvgItem(goocanvas.ItemSimple):
    # setup our custom properties
    __gproperties__ = {
        'x': (float,                                # property type
              'X',                                  # property nick name
              'The x coordinate of a SVG image',    # property description
              0,                                    # property minimum value
              10e6,                                 # property maximum value
              0,                                    # property default value
              gobject.PARAM_READWRITE),             # property flags

        'y': (float,
              'Y',
              'The y coordinate of a SVG image',
              0,
              10e6,
              0,
              gobject.PARAM_READWRITE),

        'width': (float,
                  'Width',
                  'The width of the SVG Image',
                  0,
                  10e6,
                  0,
                  gobject.PARAM_READABLE),

        'height': (float,
                   'Height',
                   'The width of the SVG Image',
                   0,
                   10e6,
                   0,
                   gobject.PARAM_READABLE),
        }
    
    def __init__(self, x, y, handle, **kwargs):
        super(CustomSvgItem, self).__init__(**kwargs)
        
        self.x = x
        self.y = y
        
        self.width = handle.props.width
        self.height = handle.props.height
        
        self.handle = handle

    def do_set_property(self, pspec, value):
        if pspec.name == 'x':
            self.x = value
            
            # make sure we update the display
            self.changed(True)
        
        elif pspec.name == 'y':
            self.y = value
            
            # make sure we update the display
            self.changed(True)
        
        else:
            raise AttributeError, 'unknown property %s' % pspec.name

    def do_get_property(self, pspec):
        if pspec.name == 'x':
            return self.x

        elif pspec.name == 'y':
            return self.y

        elif pspec.name == 'width':
            return self.width

        elif pspec.name == 'height':
            return self.height

        else:
            raise AttributeError, 'unknown property %s' % pspec.name
    
    def do_simple_paint(self, cr, bounds):
        matrix = cr.get_matrix()
        matrix.translate(self.x, self.y)
        cr.set_matrix(matrix)
        self.handle.render_cairo(cr)

    def do_simple_update(self, cr):
        self.bounds_x1 = float(self.x)
        self.bounds_y1 = float(self.y)
        self.bounds_x2 = float(self.x + self.width)
        self.bounds_y2 = float(self.y + self.height)

    def do_simple_is_item_at(self, x, y, cr, is_pointer_event):
        if ((x < self.x) or (x > self.x + self.width)) or ((y < self.y) or (y > self.y + self.height)):
            return False
        else:    
            return True

gobject.type_register(CustomSvgItem)



def on_tooltip (item, x, y, keyboard_mode, tooltip):
    tooltip.set_text(item.get_data("tooltip"))
    return True

def on_button_press(item, target_item, event):

    path = item.get_data("path_object")

    if (path.props.visibility == goocanvas.ITEM_INVISIBLE):
        path.props.visibility = goocanvas.ITEM_VISIBLE
    else:
        path.props.visibility = goocanvas.ITEM_INVISIBLE

    #path.request_update()
        

def fetch_agent_data_map ():
    command = "http://" + MASTER_IP + ":" + MASTER_REST_PORT + AGENT_RESOURCE
    json_data = urllib2.urlopen (command).read()
    data_map = json.loads (json_data)
    return data_map


def fetch_client_data_map ():
    command = "http://" + MASTER_IP + ":" + MASTER_REST_PORT + CLIENT_RESOURCE
    json_data = urllib2.urlopen (command).read()
    data_map = json.loads (json_data)
    return data_map



#def create_focus_elipse (canvas, x, y, width, height, color, name):
#    root = canvas.get_root_item ()
#    item = goocanvas.Ellipse (parent = root,
#                                  center_x = x,
#                                  center_y = y,
#                                  radius_x = width,
#                                  radius_y = height,
#                                  fill_color = color,
#                                  can_focus = True)
#    item.set_data ("id", name)
#
#    return item

def create_focus_image (canvas, x_, y_, image_file, name):
    root = canvas.get_root_item ()
     
    handle = rsvg.Handle(image_file)

    svgitem = CustomSvgItem(x=x_,
                            y=y_,
                            handle=handle,
                            parent=root)

    svgitem.set_data ("id", name)

    return svgitem




def update_client_tooltip (item, node_mac_addr, props_map):
    tooltip_str = ""
    for each in props_map.keys():
         tooltip_str +=  each + ": " + props_map[each] + "\n"

    tooltip_str = tooltip_str[:-1]
    item.set_data("tooltip", tooltip_str)


# The first time, we pull in all the node
# information from the master, instantiate
# the items, and then draw the canvas. The
# udpate_canvas() method will then update
# the items on this canvas periodically
def setup_canvas (canvas):
    global master, agent_item_map, client_item_map, point_map

    master = create_focus_image (canvas, CANVAS_WIDTH/2.0 - 30, 80 - 60, "master.svg", "Master")

    # Get list of agents from master
    agent_map = fetch_agent_data_map ()
    total_agents = len(agent_map.keys())

    i = 1
    point_map = {}

    # Align agents, and draw lines between agents and master
    for each in agent_map.keys():
        offset = (CANVAS_WIDTH * 1.0/(total_agents + 1)) * i
        path = goocanvas.Path(parent = canvas.get_root_item(),
                                  data="M %s %s L %s %s" % (CANVAS_WIDTH/2.0, 80, offset, 200))

        #item = create_focus_elipse (canvas, offset, 200, 30, 30, "red", "agent")
        item = create_focus_image (canvas, offset - 50, 150, "ap.svg", "agent")
        agent_item_map[each] = item

        i += 1
        item.set_data ("coords", (offset, 200))
        point_map[each] = [offset, 300]

    # Keep master above the lines
    master.raise_(None)

    # Get list of clients from master
    client_map = fetch_client_data_map ()

    # Draw nodes for each client. If a client
    # hasn't received an IP address (didn't follow)
    # through with the connection, then indicate
    # as so.
    for each in client_map.keys():
        if (client_map[each]["ipAddress"] != "0.0.0.0"):
            color = "green"
            if (client_map[each]["agent"] is not None):
                x = point_map["/" + client_map[each]["agent"]][0]
                y = point_map["/" + client_map[each]["agent"]][1]

                item = create_focus_image (canvas, x - 20, y - 20, "client.svg", "client-" + each)
                
                agent = agent_item_map["/" + client_map[each]["agent"]]

                if (agent != None):
                    path = goocanvas.Path(parent = canvas.get_root_item(),
                                       data="M %s %s L %s %s" % (agent.get_data("coords")[0], agent.get_data("coords")[1], x, y))
                    item.set_data ("path_object", path)
                    item.set_data ("my_coords", (x, y))
                    path.props.visibility = goocanvas.ITEM_INVISIBLE

                agent.raise_(None)
                item.raise_(None)

                client_item_map[each] = item
                point_map["/" + client_map[each]["agent"]][1] += 60
                update_client_tooltip (item, each, client_map[each])
                #item.connect ("query_tooltip",  on_tooltip)
                item.connect ("button_press_event",  on_button_press)

    return


def update_canvas (canvas):

    # Now just update
    agent_map = fetch_agent_data_map ()
    client_map = fetch_client_data_map ()

    #for each in agent_map.keys():
    #    if (each in agent_item_map):
    #        item = agent_item_map[each]

    for each in client_map.keys():
        color = "green"
        
        # For now, only show clients which followed
        # through with the connection
        if (client_map[each]["ipAddress"] == "0.0.0.0"):
            continue

        if (each in client_item_map):
          
            item = client_item_map[each]
            update_client_tooltip (item, each, client_map[each])

            agent = agent_item_map["/" + client_map[each]["agent"]]

            if (agent != None):
                item.get_data("path_object").props.data = "M %s %s L %s %s" % (agent.get_data("coords")[0], 
                                                                                agent.get_data("coords")[1],
                                                                                item.get_data("my_coords")[0], 
                                                                                item.get_data("my_coords")[1])
                #agent.raise_(None)
                item.get_data("path_object").request_update()

            item.request_update()
        #else:
        #    print each, client_map, point_map
            #x = point_map["/" + client_map[each]["agent"]][0]
            #y = point_map["/" + client_map[each]["agent"]][1]
            #item = create_focus_image (canvas, x, y, "client.svg", "client-" + each)

            #agent = agent_item_map["/" + client_map[each]["agent"]]

            #if (agent != None):
            #    path = goocanvas.Path(parent = canvas.get_root_item(),
            #                           data="M %s %s L %s %s" % (agent.get_data("coords")[0], agent.get_data("coords")[1], x, y))
            #    item.set_data ("path_object", path)
            #    item.set_data ("my_coords", (x, y))
            #    path.props.visibility = goocanvas.ITEM_INVISIBLE

            ##item.raise_(None)
            ##agent.raise_(None)

            #client_item_map[each] = item
            #point_map["/" + client_map[each]["agent"]][1] += 60
            #update_client_tooltip (item, each, client_map[each])
            ##item.connect ("query_tooltip",  on_tooltip)
            #item.connect ("button_press_event",  on_button_press)

    threading.Timer (1.0, update_canvas, [canvas]).start()


def create_focus_page ():
    vbox = gtk.VBox (False, 4)
    vbox.set_border_width (4)

    label = gtk.Label ("Odin: brought to you by the Berlin Open Wireless Lab (BOWL)")
    vbox.pack_start (label, False, False, 0)

    scrolled_win = gtk.ScrolledWindow ()
    scrolled_win.set_shadow_type (gtk.SHADOW_IN)

    vbox.add (scrolled_win)

    canvas = goocanvas.Canvas ()
    canvas.set_flags (gtk.CAN_FOCUS)
    canvas.set_size_request (CANVAS_WIDTH, 10000)
    canvas.set_bounds (0, 0, CANVAS_WIDTH, 10000)
    canvas.props.has_tooltip = False

    scrolled_win.add (canvas)
    setup_canvas (canvas)

    # start canvas update thread
    threading.Timer (1.0, update_canvas, [canvas]).start()

    return vbox


def main ():
    gtk.gdk.threads_init() # .. or we can't use timers.

    vb = create_focus_page ()
    
    win = gtk.Window ()
    win.connect ("destroy", gtk.main_quit)
    win.add (vb)
    win.show_all ()

    gtk.main ()

if __name__ == "__main__":
    main ()
