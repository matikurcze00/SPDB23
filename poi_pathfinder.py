import tkinter as tk
from tkinter import ttk
import tkintermapview
import re
from shapely.geometry import Point
import pyproj

from gui.multi_select_dropdown import MultiSelectDropdown
from poi_algorithm import run_poi_pathfinder_algorithm

class POIPathfinderGUI:
    def __init__(self):
        self.__root = tk.Tk()
        self.__root.title("POI Pathfinder")
        self.__root.resizable(False, False)

        self.__map_frame = None
        self.__map_widget = None

        self.__control_frame = None
        self.__poi_requirements_frame = None
        self.__main_var = tk.BooleanVar(value = True)
        self.__time_road_var = tk.BooleanVar(value = True)
        self.__from_var = tk.BooleanVar(value = True)

        self.__start_loc = tk.StringVar(value = "")
        self.__end_loc = tk.StringVar(value = "")
        self.__max_time_ext = tk.StringVar(value = 0.0)
        self.__max_road_ext = tk.StringVar(value = 0.0)

        self.__poi_time_road_req = tk.StringVar(value = 0.0)

        self.__selected_poi_types = []

        self.__transformer_to_4326 = pyproj.Transformer.from_crs(3857, 4326, always_xy = True)

        self.__init_map()
        self.__init_control_frame()
        self.__init_buttons()

    def run(self):
        self.__root.mainloop()

    def __init_map(self):
        self.__map_frame = tk.Frame(self.__root, width = 700, height = 550)
        self.__map_frame.pack(side = "left", fill = "both", expand = True)
        self.__map_frame.pack_propagate(False)
        self.__map_widget = tkintermapview.TkinterMapView(self.__map_frame, width = 600, height = 600, corner_radius = 0)
        self.__map_widget.pack(fill = "both", expand = True)
        self.__map_widget.set_position(52.54682, 19.70638)
        self.__map_widget.set_zoom(6)
        
    def __init_control_frame(self):
        self.__init_main_edit_fields()
        self.__init_poi_requirements_frame()

    def __init_main_edit_fields(self):
        self.__control_frame = tk.Frame(self.__root, width = 300, height = 550)
        self.__control_frame.pack(side = "right", fill = "both", expand = True)
        self.__control_frame.pack_propagate(False)

        self.__start_loc_label = tk.Label(self.__control_frame, text = "Start location")
        self.__start_loc_label.pack(pady = 2)
        self.__start_loc_edit = tk.Entry(self.__control_frame, textvariable = self.__start_loc)
        self.__start_loc_edit.pack(pady = 2)

        self.__end_loc_label = tk.Label(self.__control_frame, text = "End location")
        self.__end_loc_label.pack(pady = 2)
        self.__end_loc_edit = tk.Entry(self.__control_frame, textvariable = self.__end_loc)
        self.__end_loc_edit.pack(pady = 2)

        # Max time extension controls
        self.__max_time_frame = tk.Frame(self.__control_frame)
        self.__max_time_frame.pack(pady = 2)
        self.__max_time_radio_button = tk.Radiobutton(
            self.__max_time_frame,
            variable = self.__main_var,
            value = True,
            text = "Max. time extension [h]",
            command = self.__toggle_main_radio_button_state,
        )
        self.__max_time_radio_button.pack(side = "left")
        self.__max_time_edit = tk.Entry(self.__control_frame, textvariable = self.__max_time_ext)
        self.__max_time_edit.pack(pady = 2)
        self.__max_time_edit.config(state = "normal")

        # Max road extension controls
        self.__max_road_frame = tk.Frame(self.__control_frame)
        self.__max_road_frame.pack(pady = 2)
        self.__max_road_radio_button = tk.Radiobutton(
            self.__max_road_frame,
            variable = self.__main_var,
            value = False,
            text = "Max. road extension [km]",
            command = self.__toggle_main_radio_button_state,
        )
        self.__max_road_radio_button.pack(side = "left")
        self.__max_road_edit = tk.Entry(self.__control_frame, textvariable = self.__max_road_ext)
        self.__max_road_edit.pack(pady = 2)
        self.__max_road_edit.config(state = "disabled")

    def __init_poi_requirements_frame(self):
        self.__poi_requirements_label = tk.Label(self.__control_frame, text = "POI requirements")
        self.__poi_requirements_label.pack(pady = (10, 0))
        self.__poi_requirements_frame = tk.Frame(self.__control_frame, bg = "gray", pady = 10)
        self.__poi_requirements_frame.pack(fill = "x", padx = 10, pady = 10)

        self.__time_road_frame = tk.Frame(self.__poi_requirements_frame, bg = "gray")
        self.__time_road_frame.pack(pady = 2)
        self.__time_radio_button = tk.Radiobutton(
            self.__time_road_frame,
            text = "Time [h]",
            variable = self.__time_road_var,
            value = True,
            bg = "gray"
        )
        self.__time_radio_button.pack(side = "left")

        self.__road_radio_button = tk.Radiobutton(
            self.__time_road_frame,
            text = "Road [km]",
            variable = self.__time_road_var,
            value = False,
            bg = "gray"
        )
        self.__road_radio_button.pack(side = "right")

        self.__begin_end_frame = tk.Frame(self.__poi_requirements_frame, bg = "gray")
        self.__begin_end_frame.pack(pady = 2)
        self.__from_begin_radio_button = tk.Radiobutton(
            self.__begin_end_frame,
            text = "From beginning",
            variable = self.__from_var,
            value = True,
            bg = "gray"
        )
        self.__from_begin_radio_button.pack(side = "left")

        self.__from_end_radio_button = tk.Radiobutton(
            self.__begin_end_frame,
            text = "From end",
            variable = self.__from_var,
            value = False,
            bg = "gray"
        )
        self.__from_end_radio_button.pack(side = "right", pady = 10)

        self.__poi_time_road = tk.Entry(self.__poi_requirements_frame, textvariable = self.__poi_time_road_req)
        self.__poi_time_road.pack(pady = 2)

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

    def __toggle_main_radio_button_state(self):
        state = "normal" if self.__main_var.get() else "disabled"
        opposite_state = "disabled" if self.__main_var.get() else "normal"
        self.__max_time_edit.config(state = state)
        self.__max_road_edit.config(state = opposite_state)

    def __run_button_on_click(self):
        if not self.__check_fields():
            return
        
        parameters = {
            "start_location": self.__start_loc.get(),
            "end_location": self.__end_loc.get(),
            "max_ext_type": "time" if self.__main_var.get() else "road",
            "max_time_ext": float(self.__max_time_ext.get()),
            "max_road_ext": float(self.__max_road_ext.get()),
            "poi_requirements_type": "time" if self.__time_road_var.get() else "road",
            "poi_from_type": "begin" if self.__from_var.get() else "end", 
            "poi_from_val": float(self.__poi_time_road_req.get()),
            "poi_types": self.__selected_poi_types
        }

        msg = f"Start location: {parameters['start_location']}\nEnd Location : {parameters['end_location']}\n"
        ext_type_text = "Max. time extension [h]" if parameters["max_ext_type"] == "time" else "Max. road extension [km]"
        msg += f"{ext_type_text}: {parameters['max_road_ext']}\n"
        req_type = "time" if parameters["poi_requirements_type"] == "time" else "road"
        msg += f"POI requirements ({req_type}):\n"
        position = "From beginning" if parameters["poi_from_type"] == "begin" else "From end"
        msg += f"   {position}: {parameters['poi_from_val']}\n"
        msg += f"POI types: {parameters['poi_types']}"

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
            (self.__start_loc.get() in [None, ""], "Start location was not defined!"),
            (self.__end_loc.get() in [None, ""], "End location was not defined!"),
            (self.__max_time_ext.get() == "", "Max. time extension was not defined!"),
            (not self.__is_float(self.__max_time_ext.get()), "Max. time extension needs to be a number"),
            (float(self.__max_time_ext.get()) < 0.0, "Max. time extension can not be less than 0!"),
            (self.__max_road_ext.get() == "", "Max. road extension was not defined!"),
            (not self.__is_float(self.__max_road_ext.get()), "Max. road extension needs to be a number!"),
            (float(self.__max_road_ext.get()) < 0.0, "Max. road extension can not be less than 0!"),
            (self.__time_road_var.get() and self.__from_var.get() and self.__poi_time_road_req.get() == "", "Road from beginning was not defined!"),
            (self.__time_road_var.get() and self.__from_var.get() and  not self.__is_float(self.__poi_time_road_req.get()), "Road from beginning needs to be a number!"),
            (self.__time_road_var.get() and self.__from_var.get() and  float(self.__poi_time_road_req.get()) < 0.0, "Road from beginning can not be less than 0!"),
            (self.__time_road_var.get() and not self.__from_var.get() and  self.__poi_time_road_req.get() == "", "Road from end was not defined!"),
            (self.__time_road_var.get() and not self.__from_var.get() and  not self.__is_float(self.__poi_time_road_req.get()), "Road from end needs to be a number!"),
            (self.__time_road_var.get() and not self.__from_var.get() and  float(self.__poi_time_road_req.get()) < 0.0, "Road from end can not be less than 0!"),
            (not self.__time_road_var.get() and self.__from_var.get() and self.__poi_time_road_req.get() == "", "Time from beginning was not defined!"),
            (not self.__time_road_var.get() and self.__from_var.get() and not self.__is_float(self.__poi_time_road_req.get()), "Time from beginning needs to be a number!"),
            (not self.__time_road_var.get() and self.__from_var.get() and float(self.__poi_time_road_req.get()) < 0.0, "Time from beginning can not be less than 0!"),
            (not self.__time_road_var.get() and not self.__from_var.get() and self.__poi_time_road_req.get() == "", "Time from end was not defined!"),
            (not self.__time_road_var.get() and not self.__from_var.get() and not self.__is_float(self.__poi_time_road_req.get()), "Time from end needs to be a number!"),
            (not self.__time_road_var.get() and not self.__from_var.get() and float(self.__poi_time_road_req.get()) < 0.0, "Time from end can not be less than 0!"),
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

    def __clear_map(self):
        self.__map_widget.delete_all_path()
        self.__map_widget.delete_all_marker()

    def __run_algorithm(self, parameters):
        self.__clear_map()
        path, poi_point = run_poi_pathfinder_algorithm(parameters)

        if path == None:
            print("[ERROR] Algorithm failed to create a path, because a given POI type could not be found.")
            tk.messagebox.showwarning("Error", "Failed to find a given POI type for given parameters.")
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
        poi_x_coord, poi_y_coord = self.__transformer_to_4326.transform(poi_point.x, poi_point.y)

        start_marker = self.__map_widget.set_marker(start_y_coord, start_x_coord)
        start_marker.set_position(start_y_coord, start_x_coord)
        end_marker = self.__map_widget.set_marker(end_y_coord, end_x_coord)
        end_marker.set_position(end_y_coord, end_x_coord)
        poi_marker = self.__map_widget.set_marker(poi_y_coord, poi_x_coord, text = "POI", marker_color_outside = "blue", marker_color_circle = "yellow")
        poi_marker.set_position(poi_y_coord, poi_x_coord)

        self.__map_widget.set_position((start_y_coord + end_y_coord) / 2, (start_x_coord + end_x_coord) / 2)
        self.__map_widget.set_zoom(9)
        self.__map_widget.update_canvas_tile_images()

if __name__ == "__main__":
    gui = POIPathfinderGUI()
    gui.run()