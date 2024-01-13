import tkinter as tk
from tkinter import ttk
import tkintermapview

from gui.multi_select_dropdown import MultiSelectDropdown

def read_poi_types_form_file(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file.readlines()]
    
def receive_selected_options(selected_options):
    print("Selected options:", selected_options)

root = tk.Tk()
root.title("POI Pathfinder")
root.resizable(False, False)

map_frame = tk.Frame(root, width = 600, height = 600)
map_frame.pack(side = "left", fill = "both", expand = True)
map_frame.pack_propagate(False)

map_widget = tkintermapview.TkinterMapView(map_frame, width = 600, height = 600, corner_radius = 0)
map_widget.pack(fill = "both", expand = True)

control_frame = tk.Frame(root, width = 400, height = 600)
control_frame.pack(side = "right", fill = "both", expand = True)
control_frame.pack_propagate(False)

start_loc_label = tk.Label(root, text = "Starting location")
start_loc_label.pack(pady = 2)
start_loc_edit = tk.Entry(control_frame)
start_loc_edit.pack(pady = 2)

end_loc_label = tk.Label(root, text = "End location")
end_loc_label.pack(pady = 2)
end_loc_edit = tk.Entry(control_frame)
end_loc_edit.pack(pady = 2)

max_time_label = tk.Label(root, text = "Max. time extension [h]")
max_time_label.pack(pady = 2)
max_time_edit = tk.Entry(control_frame)
max_time_edit.pack(pady = 2)

max_path_label = tk.Label(root, text = "Max. path extension [km]")
max_path_label.pack(pady = 2)
max_path_edit = tk.Entry(control_frame)
max_path_edit.pack(pady = 2)

poi_requirements_label = tk.Label(control_frame, text = "POI requirements")
poi_requirements_label.pack(pady = (10, 0))
poi_requirements_box = tk.Frame(control_frame, bg = "gray", pady = 10)
poi_requirements_box.pack(fill = "x", padx = 10, pady = 10)

var = tk.BooleanVar(value = True)

def toggle_state():
    state = "normal" if var.get() else "disabled"
    opposite_state = "disabled" if var.get() else "normal"
    road_from_begin_edit.config(state = state)
    road_from_end_edit.config(state = state)
    time_from_begin_edit.config(state = opposite_state)
    time_from_end_edit.config(state = opposite_state)

road_radio_button = tk.Radiobutton(
    poi_requirements_box,
    text = "Road",
    variable = var,
    value = True,
    command = toggle_state,
    bg = "gray"
)
road_radio_button.pack()

road_from_begin_label = tk.Label(poi_requirements_box, text = "From beginning", bg = "gray")
road_from_begin_label.pack(pady = 2)
road_from_begin_edit = tk.Entry(poi_requirements_box)
road_from_begin_edit.pack(pady = 2)
road_from_begin_edit.config(state = "normal")

road_from_end_label = tk.Label(poi_requirements_box, text = "From end", bg = "gray")
road_from_end_label.pack(pady = 2)
road_from_end_edit = tk.Entry(poi_requirements_box)
road_from_end_edit.pack(pady = 2)
road_from_end_edit.config(state = "normal")

time_radio_button = tk.Radiobutton(
    poi_requirements_box,
    text = "Time",
    variable = var,
    value = False,
    command = toggle_state,
    bg = "gray"
)
time_radio_button.pack()

time_from_begin_label = tk.Label(poi_requirements_box, text = "From beginning", bg = "gray")
time_from_begin_label.pack(pady = 2)
time_from_begin_edit = tk.Entry(poi_requirements_box)
time_from_begin_edit.pack(pady = 2)
time_from_begin_edit.config(state = "disabled")

time_from_end_label = tk.Label(poi_requirements_box, text = "From end", bg = "gray")
time_from_end_label.pack(pady = 2)
time_from_end_edit = tk.Entry(poi_requirements_box)
time_from_end_edit.pack(pady = 2)
time_from_end_edit.config(state = "disabled")

poi_type_label = tk.Label(poi_requirements_box, text = "POI type", bg = "gray")
poi_type_label.pack(pady = 2)
poi_types = read_poi_types_form_file("poi_types.txt")
multi_select_dd = MultiSelectDropdown(poi_requirements_box, poi_types, on_selection_done = receive_selected_options)

button_frame = tk.Frame(control_frame)
button_frame.pack(side = "bottom", fill = "x", pady = 10)
button_frame.pack_propagate(False)
button_frame.config(height = 40)

run_button = tk.Button(control_frame, text = "Run", bg = "green", height = 2, width = 10)
run_button.pack(side = "left", padx = 10)

exit_button = tk.Button(control_frame, text = "Exit", bg = "red", height = 2, width = 10, command = root.destroy)
exit_button.pack(side = "left", padx = 10)

root.mainloop()
