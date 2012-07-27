import goocanvas
import gtk
import urllib2
import json
import time
import threading


MASTER_IP = "172.17.255.103"
MASTER_REST_PORT = "8080"
CLIENT_RESOURCE = "/odin/clients/json"
AGENT_RESOURCE = "/odin/agents/json"
SPACING = 10
CANVAS_WIDTH = 1000

master = None
agent_item_map = {}
client_item_map =  {}

def on_tooltip (item, x, y, keyboard_mode, tooltip):
    tooltip.set_text(item.get_data("tooltip"))
    return True


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



def create_focus_elipse (canvas, x, y, width, height, color, name):
    root = canvas.get_root_item ()
    item = goocanvas.Ellipse (parent = root,
                                  center_x = x,
                                  center_y = y,
                                  radius_x = width,
                                  radius_y = height,
                                  fill_color = color,
                                  can_focus = True)
    item.set_data ("id", name)

    return item


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

    master = create_focus_elipse (canvas, CANVAS_WIDTH/2.0, 80, 30, 30, "blue", "Master")

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

        item = create_focus_elipse (canvas, offset, 200, 30, 30, "red", "agent")
        agent_item_map[each] = item

        i += 1
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
        #     color = "yellow"
        # else:
        #     color = "green"
            color = "green"
            if (client_map[each]["agent"] is not None):
                item = create_focus_elipse (canvas, point_map["/" + client_map[each]["agent"]][0], point_map["/" + client_map[each]["agent"]][1], 15, 15, color, "client-" + each)
                client_item_map[each] = item
                point_map["/" + client_map[each]["agent"]][1] += 60
                update_client_tooltip (item, each, client_map[each])
                item.connect ("query_tooltip",  on_tooltip)

    return


def update_canvas (canvas):

    # Now just update
    agent_map = fetch_agent_data_map ()
    client_map = fetch_client_data_map ()

    for each in agent_map.keys():
        if (each in agent_item_map):
            item = agent_item_map[each]

    for each in client_map.keys():
        color = "green"
        
        # For now, only show clients which followed
        # through with the connection
        if (client_map[each]["ipAddress"] == "0.0.0.0"):
            continue

        if (each in client_item_map):
            item = client_item_map[each]
            update_client_tooltip (item, each, client_map[each])
            item.props.fill_color = color
            item.request_update()
        else:
            item = create_focus_elipse (canvas, point_map["/" + client_map[each]["agent"]][0], point_map["/" + client_map[each]["agent"]][1], 15, 15, color, "client-" + each)
            client_item_map[each] = item
            point_map["/" + client_map[each]["agent"]][1] += 60
            update_client_tooltip (item, each, client_map[each])
            item.connect ("query_tooltip",  on_tooltip)

    threading.Timer (1, update_canvas, [canvas]).start()


def create_focus_page ():
    vbox = gtk.VBox (False, 4)
    vbox.set_border_width (4)

    label = gtk.Label ("Odin: brought to you by Shark, Shark, and Sharks (TM)")
    vbox.pack_start (label, False, False, 0)

    scrolled_win = gtk.ScrolledWindow ()
    scrolled_win.set_shadow_type (gtk.SHADOW_IN)

    vbox.add (scrolled_win)

    canvas = goocanvas.Canvas ()
    canvas.set_flags (gtk.CAN_FOCUS)
    canvas.set_size_request (CANVAS_WIDTH, 10000)
    canvas.set_bounds (0, 0, CANVAS_WIDTH, 10000)
    canvas.props.has_tooltip = True

    scrolled_win.add (canvas)
    setup_canvas (canvas)

    # start canvas update thread
    threading.Timer (1, update_canvas, [canvas]).start()

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