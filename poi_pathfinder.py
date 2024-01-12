import tkinter as tk
from tkinter import ttk
import tkintermapview


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

label = tk.Label(root, text = "Starting location")
label.pack(pady = 2)
edit_field1 = tk.Entry(control_frame)
edit_field1.pack(pady = 2)

label = tk.Label(root, text = "End location")
label.pack(pady = 2)
edit_field2 = tk.Entry(control_frame)
edit_field2.pack(pady = 2)

label = tk.Label(root, text = "Max. time extension [h]")
label.pack(pady = 2)
edit_field3 = tk.Entry(control_frame)
edit_field3.pack(pady = 2)

label = tk.Label(root, text = "Max. path extension [km]")
label.pack(pady = 2)
edit_field4 = tk.Entry(control_frame)
edit_field4.pack(pady = 2)

label = tk.Label(control_frame, text = "POI requirements")
label.pack(pady = (10, 0))
gray_box = tk.Frame(control_frame, bg = "gray", pady = 10)
gray_box.pack(fill = "x", padx = 10, pady = 10)

var = tk.BooleanVar(value = True)

def toggle_state():
    state = "normal" if var.get() else "disabled"
    opposite_state = "disabled" if var.get() else "normal"
    edit_field5.config(state = state)
    edit_field6.config(state = state)
    edit_field7.config(state = opposite_state)
    edit_field8.config(state = opposite_state)

radio_button1 = tk.Radiobutton(
    gray_box,
    text = "Road",
    variable = var,
    value = True,
    command = toggle_state,
    bg = "gray"
)
radio_button1.pack()

label = tk.Label(gray_box, text = "From beginning", bg = "gray")
label.pack(pady = 2)
edit_field5 = tk.Entry(gray_box)
edit_field5.pack(pady = 2)
edit_field5.config(state = "normal")

label = tk.Label(gray_box, text = "From end", bg = "gray")
label.pack(pady = 2)
edit_field6 = tk.Entry(gray_box)
edit_field6.pack(pady = 2)
edit_field6.config(state = "normal")

radio_button2 = tk.Radiobutton(
    gray_box,
    text = "Time",
    variable = var,
    value = False,
    command = toggle_state,
    bg = "gray"
)
radio_button2.pack()

label = tk.Label(gray_box, text = "From beginning", bg = "gray")
label.pack(pady = 2)
edit_field7 = tk.Entry(gray_box)
edit_field7.pack(pady = 2)
edit_field7.config(state = "disabled")

label = tk.Label(gray_box, text = "From end", bg = "gray")
label.pack(pady = 2)
edit_field8 = tk.Entry(gray_box)
edit_field8.pack(pady = 2)
edit_field8.config(state = "disabled")

label = tk.Label(gray_box, text = "POI type", bg = "gray")
label.pack(pady = 2)
dropdown_options = ["Fast food", "Option 2", "Option 3"]
dropdown_var = tk.StringVar()
dropdown = ttk.OptionMenu(gray_box, dropdown_var, dropdown_options[0], *dropdown_options)
dropdown.pack()

button_frame = tk.Frame(control_frame)
button_frame.pack(side = "bottom", fill = "x", pady = 10)
button_frame.pack_propagate(False)
button_frame.config(height = 40)

run_button = tk.Button(control_frame, text = "Run", bg = "green", height = 2, width = 10)
run_button.pack(side = "left", padx = 10)

exit_button = tk.Button(control_frame, text = "Exit", bg = "red", height = 2, width = 10, command = root.destroy)
exit_button.pack(side = "left", padx = 10)

root.mainloop()