import goocanvas
import gtk
import urllib2
import json


MASTER_IP = "172.17.255.103"
MASTER_REST_PORT = "8080"
CLIENT_RESOURCE = "/odin/clients/json"
AGENT_RESOURCE = "/odin/agents/json"
SPACING = 10
CANVAS_WIDTH = 1000


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
                                  can_focus = False)
    item.set_data ("id", name)
    
    return item
    #item.connect ("focus_in_event", on_focus_in)
    #item.connect ("focus_out_event", on_focus_out)
    #item.connect ("button_press_event", on_button_press)
    #item.connect ("key_press_event",  on_key_press)


def setup_canvas (canvas):
    master = create_focus_elipse (canvas, CANVAS_WIDTH/2.0, 80, 30, 30, "blue", "Master")

    # Get list of agents from master
    agent_map = fetch_agent_data_map ()
    print agent_map
    total_agents = len(agent_map.keys())

    i = 1
    point_map = {}
    for each in agent_map.keys():
        offset = (CANVAS_WIDTH * 1.0/(total_agents + 1)) * i
        path = goocanvas.Path(parent = canvas.get_root_item(),
                                  data="M %s %s L %s %s" % (CANVAS_WIDTH/2.0, 80, offset, 200))

        create_focus_elipse (canvas, offset, 200, 30, 30, "red", "agent")

        i += 1
        point_map[each] = [offset, 300]

    master.raise_(None)
    # Get list of clients from master
    client_map = fetch_client_data_map ()

    for each in client_map.keys():
        if (client_map[each]["ipAddress"] == "0.0.0.0"):
            color = "yellow"
        else:
            color = "green"
        create_focus_elipse (canvas, point_map["/" + client_map[each]["agent"]][0], point_map["/" + client_map[each]["agent"]][1], 15, 15, color, "client-" + each)
        point_map["/" + client_map[each]["agent"]][1] += 60

    return

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
    canvas.set_size_request (CANVAS_WIDTH, 1000)
    canvas.set_bounds (0, 0, CANVAS_WIDTH, 1000)

    scrolled_win.add (canvas)

    setup_canvas (canvas)

    return vbox


def main ():
    vb = create_focus_page ()
    
    win = gtk.Window ()
    win.connect ("destroy", gtk.main_quit)
    win.add (vb)
    win.show_all ()

    gtk.main ()

if __name__ == "__main__":
    main ()
