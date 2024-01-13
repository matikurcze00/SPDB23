import tkinter as tk
from tkinter import ttk

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient = "vertical", command = canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion = canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window = self.scrollable_frame, anchor = "nw")
        canvas.configure(yscrollcommand = scrollbar.set)
        canvas.pack(side = "left", fill = "both", expand = True)
        scrollbar.pack(side = "right", fill = "y")

class MultiSelectDropdown:
    def __init__(self, parent, options, on_selection_done = None):
        self.parent = parent
        self.options = options
        self.selected_options = []
        self.check_vars = {}

        self.display_button = tk.Button(parent, text = "Select POI types", command = self.show_options)
        self.display_button.pack()

        self.selection_window = None
        self.on_selection_done = on_selection_done

    def show_options(self):
        if self.selection_window:
            return
        
        self.selection_window = tk.Toplevel(self.parent)
        self.selection_window.title("Select POI types")
        self.selection_window.geometry("400x400")
        self.selection_window.resizable(False, False)

        scroll_frame = ScrollableFrame(self.selection_window)
        scroll_frame.pack(fill = "both", expand = True)

        for option in self.options:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(scroll_frame.scrollable_frame, text = option, variable = var)
            cb.pack(anchor = "w")
            self.check_vars[option] = var
        
        close_button = tk.Button(self.selection_window, text = "Done", command = self.close_window)
        close_button.pack()

    def close_window(self):
        self.selected_options = [option for option, var in self.check_vars.items() if var.get()]
        if self.on_selection_done:
            self.on_selection_done(self.selected_options)
        self.selection_window.destroy()
        self.selection_window = None
