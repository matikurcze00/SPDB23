import tkinter as tk
from tkinter import ttk
import tkintermapview
import re
from shapely.geometry import Point
import pyproj

from gui.multi_select_dropdown import MultiSelectDropdown
from poi_algorithm import run_poi_pathfinder_algorithm

from geopy.geocoders import Nominatim

class POIPathfinderGUI:
    def __init__(self):
        self.__root = tk.Tk()
        self.__root.title("POI Pathfinder")
        self.__root.resizable(False, False)

        self.__map_frame = None
        self.__map_widget = None
        self.__control_frame = None
        self.__poi_requirements_frame = None
        self.__var = tk.BooleanVar(value = True)

        self.__starting_loc = tk.StringVar(value = "")
        self.__end_loc = tk.StringVar(value = "")
        self.__max_time_ext = tk.StringVar(value = 0.0)
        self.__max_road_ext = tk.StringVar(value = 0.0)

        self.__poi_from_begin_road = tk.StringVar(value = 0.0)
        self.__poi_from_end_road = tk.StringVar(value = 0.0)
        self.__poi_from_begin_time = tk.StringVar(value = 0.0)
        self.__poi_from_end_time = tk.StringVar(value = 0.0)

        self.__selected_poi_types = []

        self.__transformer_to_3857 = pyproj.Transformer.from_crs(4326, 3857, always_xy = True)
        self.__transformer_to_4326 = pyproj.Transformer.from_crs(3857, 4326, always_xy = True)

        self.__init_map()
        self.__init_control_frame()
        self.__init_buttons()

    def run(self):
        self.__root.mainloop()

    def __init_map(self):
        self.__map_frame = tk.Frame(self.__root, width = 600, height = 600)
        self.__map_frame.pack(side = "left", fill = "both", expand = True)
        self.__map_frame.pack_propagate(False)
        self.__map_widget = tkintermapview.TkinterMapView(self.__map_frame, width = 600, height = 600, corner_radius = 0)
        self.__map_widget.pack(fill = "both", expand = True)
        
    def __init_control_frame(self):
        self.__init_main_edit_fields()
        self.__init_poi_requirements_frame()

    def __init_main_edit_fields(self):
        self.__control_frame = tk.Frame(self.__root, width = 400, height = 600)
        self.__control_frame.pack(side = "right", fill = "both", expand = True)
        self.__control_frame.pack_propagate(False)

        self.__start_loc_label = tk.Label(self.__root, text = "Starting location")
        self.__start_loc_label.pack(pady = 2)
        self.__start_loc_edit = tk.Entry(self.__control_frame, textvariable = self.__starting_loc)
        self.__start_loc_edit.pack(pady = 2)

        self.__end_loc_label = tk.Label(self.__root, text = "End location")
        self.__end_loc_label.pack(pady = 2)
        self.__end_loc_edit = tk.Entry(self.__control_frame, textvariable = self.__end_loc)
        self.__end_loc_edit.pack(pady = 2)

        self.__max_time_label = tk.Label(self.__root, text = "Max. time extension [h]")
        self.__max_time_label.pack(pady = 2)
        self.__max_time_edit = tk.Entry(self.__control_frame, textvariable = self.__max_time_ext)
        self.__max_time_edit.pack(pady = 2)

        self.__max_road_label = tk.Label(self.__root, text = "Max. road extension [km]")
        self.__max_road_label.pack(pady = 2)
        self.__max_road_edit = tk.Entry(self.__control_frame, textvariable = self.__max_road_ext)
        self.__max_road_edit.pack(pady = 2)

    def __init_poi_requirements_frame(self):
        self.__poi_requirements_label = tk.Label(self.__control_frame, text = "POI requirements")
        self.__poi_requirements_label.pack(pady = (10, 0))
        self.__poi_requirements_frame = tk.Frame(self.__control_frame, bg = "gray", pady = 10)
        self.__poi_requirements_frame.pack(fill = "x", padx = 10, pady = 10)
        self.__road_radio_button = tk.Radiobutton(
            self.__poi_requirements_frame,
            text = "Road",
            variable = self.__var,
            value = True,
            command = self.__toggle_radio_button_state,
            bg = "gray"
        )
        self.__road_radio_button.pack()

        self.__road_from_begin_label = tk.Label(self.__poi_requirements_frame, text = "From beginning", bg = "gray")
        self.__road_from_begin_label.pack(pady = 2)
        self.__road_from_begin_edit = tk.Entry(self.__poi_requirements_frame, textvariable = self.__poi_from_begin_road)
        self.__road_from_begin_edit.pack(pady = 2)
        self.__road_from_begin_edit.config(state = "normal")

        self.__road_from_end_label = tk.Label(self.__poi_requirements_frame, text = "From end", bg = "gray")
        self.__road_from_end_label.pack(pady = 2)
        self.__road_from_end_edit = tk.Entry(self.__poi_requirements_frame, textvariable = self.__poi_from_end_road)
        self.__road_from_end_edit.pack(pady = 2)
        self.__road_from_end_edit.config(state = "normal")

        self.__time_radio_button = tk.Radiobutton(
            self.__poi_requirements_frame,
            text = "Time",
            variable = self.__var,
            value = False,
            command = self.__toggle_radio_button_state,
            bg = "gray"
        )
        self.__time_radio_button.pack()

        self.__time_from_begin_label = tk.Label(self.__poi_requirements_frame, text = "From beginning", bg = "gray")
        self.__time_from_begin_label.pack(pady = 2)
        self.__time_from_begin_edit = tk.Entry(self.__poi_requirements_frame, textvariable = self.__poi_from_begin_time)
        self.__time_from_begin_edit.pack(pady = 2)
        self.__time_from_begin_edit.config(state = "disabled")

        self.__time_from_end_label = tk.Label(self.__poi_requirements_frame, text = "From end", bg = "gray")
        self.__time_from_end_label.pack(pady = 2)
        self.__time_from_end_edit = tk.Entry(self.__poi_requirements_frame, textvariable = self.__poi_from_end_time)
        self.__time_from_end_edit.pack(pady = 2)
        self.__time_from_end_edit.config(state = "disabled")

        poi_types = self.__read_poi_types_form_file("gui/poi_types.txt")
        self.__multi_select_dd = MultiSelectDropdown(self.__poi_requirements_frame, poi_types, on_selection_done = self.__receive_selected_options)

    def __init_buttons(self):
        self.__button_frame = tk.Frame(self.__control_frame)
        self.__button_frame.pack(side = "bottom", fill = "x", pady = 10)
        self.__button_frame.pack_propagate(False)
        self.__button_frame.config(height = 40)

        self.__run_button = tk.Button(self.__control_frame, text = "Run", bg = "green", height = 2, width = 10, command = self.__run_button_on_click)
        self.__run_button.pack(side = "left", padx = 10)

        self.__exit_button = tk.Button(self.__control_frame, text = "Exit", bg = "red", height = 2, width = 10, command = self.__root.destroy)
        self.__exit_button.pack(side = "left", padx = 10)

    def __read_poi_types_form_file(self, file_path):
        with open(file_path, "r") as file:
            return [line.strip() for line in file.readlines()]
    
    def __receive_selected_options(self, selected_options):
        self.__selected_poi_types = selected_options

    def __toggle_radio_button_state(self):
        state = "normal" if self.__var.get() else "disabled"
        opposite_state = "disabled" if self.__var.get() else "normal"
        self.__road_from_begin_edit.config(state = state)
        self.__road_from_end_edit.config(state = state)
        self.__time_from_begin_edit.config(state = opposite_state)
        self.__time_from_end_edit.config(state = opposite_state)

    def __run_button_on_click(self):
        if not self.__check_fields():
            return
        
        parameters = {
            "starting_location": self.__starting_loc.get(),
            "end_location": self.__end_loc.get(),
            "max_time_ext": self.__max_time_ext.get(),
            "max_road_ext": self.__max_road_ext.get(),
            "poi_requirements_type": "road" if self.__starting_loc.get() else "time",
            "poi_from_begin_road": self.__poi_from_begin_road.get(),
            "poi_from_end_road": self.__poi_from_begin_road.get(),
            "poi_from_begin_time": self.__poi_from_begin_road.get(),
            "poi_from_end_time": self.__poi_from_begin_road.get(),
            "poi_types": self.__selected_poi_types
        }

        msg = f"Starting location: {self.__starting_loc.get()}\nEnd Location : {self.__end_loc.get()}\n"
        msg += f"Max. time extension [h]: {self.__max_time_ext.get()}\nMax. road extension [km]: {self.__max_road_ext.get()}\n"
        if self.__var.get():
            msg += f"POI requirements (road):\n"
            msg += f"    From beginning: {self.__poi_from_begin_road.get()}\n"
            msg += f"    From end: {self.__poi_from_end_road.get()}\n"
        else:
            msg += f"POI requirements (time):\n"
            msg += f"    From beginning: {self.__poi_from_begin_time.get()}\n"
            msg += f"    From end: {self.__poi_from_end_time.get()}\n"

        msg += f"POI types: {self.__selected_poi_types}"

        print("---------------PARAMETERS---------------")
        print(msg)
        print("----------------------------------------")
        print("Running algorithm...")
        self.__run_algorithm(parameters)
        print("Algorithm finished!")

    def __check_fields(self) -> bool:
        fields_ok = True
        message = ""

        conditions = [
            (self.__starting_loc.get() in [None, ""], "Starting location was not defined!"),
            (self.__end_loc.get() in [None, ""], "End location was not defined!"),
            (self.__max_time_ext.get() == "", "Max. time extension was not defined!"),
            (not self.__is_float(self.__max_time_ext.get()), "Max. time extension needs to be a number"),
            (float(self.__max_time_ext.get()) < 0.0, "Max. time extension can not be less than 0!"),
            (self.__max_road_ext.get() == "", "Max. road extension was not defined!"),
            (not self.__is_float(self.__max_road_ext.get()), "Max. road extension needs to be a number!"),
            (float(self.__max_road_ext.get()) < 0.0, "Max. road extension can not be less than 0!"),
            (False if self.__var.get() else self.__poi_from_begin_road.get() == "", "Road from beginning was not defined!"),
            (False if self.__var.get() else not self.__is_float(self.__poi_from_begin_road.get()), "Road from beginning needs to be a number!"),
            (False if self.__var.get() else float(self.__poi_from_begin_road.get()) < 0.0, "Road from beginning can not be less than 0!"),
            (False if self.__var.get() else self.__poi_from_end_road.get() == "", "Road from end was not defined!"),
            (False if self.__var.get() else not self.__is_float(self.__poi_from_end_road.get()), "Road from end needs to be a number!"),
            (False if self.__var.get() else float(self.__poi_from_end_road.get()) < 0.0, "Road from end can not be less than 0!"),
            (False if not self.__var.get() else self.__poi_from_begin_time.get() == "", "Time from beginning was not defined!"),
            (False if not self.__var.get() else not self.__is_float(self.__poi_from_begin_time.get()), "Time from beginning needs to be a number!"),
            (False if not self.__var.get() else float(self.__poi_from_begin_time.get()) < 0.0, "Time from beginning can not be less than 0!"),
            (False if not self.__var.get() else self.__poi_from_end_time.get() == "", "Time from end was not defined!"),
            (False if not self.__var.get() else not self.__is_float(self.__poi_from_end_time.get()), "Time from end needs to be a number!"),
            (False if not self.__var.get() else float(self.__poi_from_end_time.get()) < 0.0, "Time from end can not be less than 0!"),
            (len(self.__selected_poi_types) == 0, "At least one POI type needs to be selected!"),
        ]

        for condition, msg in conditions:
            if condition:
                fields_ok = False
                message = msg
                break

        if not fields_ok:
            fields_ok = False
            tk.messagebox.showwarning("Warning", message)

        return fields_ok

    def __is_float(self, value: str) -> bool:
        if re.match(r'^-?\d+(?:\.\d+)?$', value):
            return True
        else:
            return False

    def __run_algorithm(self, parameters):
        geolocator = Nominatim(user_agent = "poi_pathfinder_app")
        location = geolocator.geocode(parameters["starting_location"])
        if location:
            print(location.latitude, location.longitude)
            point = Point(location.longitude, location.latitude)

            self.__map_widget.set_position(point.y, point.x)
            self.__map_widget.set_zoom(9)

            marker = self.__map_widget.set_marker(point.y, point.x)
            marker.set_position(point.y, point.x)
        else:
            print("error")

        return # TODO TODO TODO TODO
    
        # pass start and end point names in parameters and convert them to langitude and longitude inside the algorithm function!!! 
        path = run_poi_pathfinder_algorithm(parameters)

        if path == None:
            return

        # Marking the whole road on the map
        road_cords = list()
        for i in range(len(path)):
            point = Point(path[i])
            point_x_coord, point_y_coord = self.__transformer_to_4326.transform(point.x, point.y)
            road_cords.append((point_y_coord, point_x_coord))

        self.__map_widget.set_path(road_cords)

        # Marking start and end point on the map
        start_point = Point(path[0])
        end_point = Point(path[-1])

        start_x_coord, start_y_coord = self.__transformer_to_4326.transform(start_point.x, start_point.y)
        end_x_coord, end_y_coord = self.__transformer_to_4326.transform(end_point.x, end_point.y)

        marker_1 = self.__map_widget.set_marker(start_y_coord, start_x_coord)
        marker_1.set_position(start_y_coord, start_x_coord)
        marker_2 = self.__map_widget.set_marker(end_y_coord, end_x_coord)
        marker_2.set_position(end_y_coord, end_x_coord)

        self.__map_widget.set_position((start_y_coord + end_y_coord) / 2, (start_x_coord + end_x_coord) / 2)

if __name__ == "__main__":
    gui = POIPathfinderGUI()
    gui.run()