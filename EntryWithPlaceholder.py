import tkinter as tk

class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master, textvariable, placeholder, edit_end_proc, color='grey'):
        super().__init__(master, textvariable=textvariable)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self.edit_end_proc = edit_end_proc

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)
        self.bind("<Return>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.delete('0', 'end')
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            if self.get() == self.placeholder:
                self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if len(self.get()) == 0:
            self.put_placeholder()
        else:
            self.edit_end_proc(self.get())