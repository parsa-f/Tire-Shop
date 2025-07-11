from customtkinter import *
from math import cos, pi, sin
from typing import Iterator
from awesometkinter.bidirender import add_bidi_support_for_entry, isarabic, derender_text, render_text, is_neutral

# A customized CTkButton with a predefined style and bidi text support.
class Btn(CTkButton):
    def __init__(self, master, width, height, corner_radius=20, text='', **kwargs):
        super().__init__(master, **kwargs)
        # If the text is Arabic, render it correctly for right-to-left display.
        if isarabic(text):
            text = render_text(text)
        # Apply a consistent style for buttons across the application.
        self.configure(text=text, corner_radius = corner_radius, fg_color='#AFB3ED', hover_color='#888bba', text_color='#494A5F', border_color='#8688B0')
        self.configure(width=width, height=height)
        
    def disable_hover(self):
        self.configure(hover=False)
        
    def set_text(self, text):
        if isarabic(text):
            text = render_text(text)
        self.configure(text=text)


# A customized CTkEntry with advanced features like character limits,
# bidi text support, and placeholder handling.
class Input(CTkEntry):
    def __init__(self,master, corner_radius, width, height, placeholder_text,textvariable:StringVar, show=None, char_limit:int=20, show_err_callback=None, err_message=None, placeholder_empty=True,just_text=False, just_english:bool=False,just_number=False, **kwargs):
        super().__init__(master=master,corner_radius=corner_radius, width=width, height=height, placeholder_text=placeholder_text,show=show, **kwargs)
        # Enable bidi support for right-to-left languages within the entry widget.
        add_bidi_support_for_entry(self._entry)
        
        # Apply a consistent style for input fields.
        self.configure(fg_color='#646691', placeholder_text_color='#9495B8', text_color='#c5c6de', border_color='#8688B0')

        self.char_limit = char_limit
        self.textvariable = textvariable
        self.show_err_callback = show_err_callback # A callback function to display validation errors in the UI.
        self.err_message = err_message
        self.placeholder_text = placeholder_text
        self.placeholder_empty = placeholder_empty # If True, get() returns "" when the placeholder is visible.
        self.just_english = just_english
        self.just_number = just_number
        self.just_text = just_text
        
        # Set up the validation and behavior by binding callbacks to the textvariable.
        self._set_limit()
        self._set_just_english()
        self._set_justify()
        self._set_just_number()
        self._set_just_text()
        
        
    def disable(self):
        self.configure(state='disabled')
        
    def enable(self):
        self.configure(state='normal')
    
    def set_textvariable(self, textvariable):
        self.textvariable = textvariable
        self.configure(textvariable=textvariable)
        
        # Display the placeholder text initially if it exists.
        if self.placeholder_text:
            self.textvariable.set(self.placeholder_text)
        self._set_limit()
        self._set_just_english()
        self._set_justify()
        self._set_just_number()
        self._set_just_text()
        
        
    # This callback is triggered by trace_add whenever the entry's text is changed.
    def _entry_update_callback(self, *k):
        val = self.textvariable.get()
        # Enforces the character limit by trimming the string if it's too long.
        if len(val) > self.char_limit:
            self.textvariable.set(val[0:-1])
        
            # If an error callback is provided, call it to notify the user.
            if self.show_err_callback:
                if self.err_message:
                    self.show_err_callback(self.err_message)
                else:
                    message = render_text("بیش از حد بودن کاراکتر های وارد شده")
                    self.show_err_callback(message)
    
    # Binds the character limit validation to the textvariable's 'write' event.
    def _set_limit(self):
        self.textvariable.trace_add('write', self._entry_update_callback)
    
    # Callback to automatically adjust text justification based on the first character's language.

    def _add_justify_for_arabic(self, *k):
        val = self.textvariable.get()
        if len(val) == 1:
            if isarabic(val):
                self.configure(justify=RIGHT)
            else:
                self.configure(justify=LEFT)
                
    # Binds the justification callback if multilingual input is allowed.
    def _set_justify(self):
        if not self.just_english:
            self.textvariable.trace_add('write', self._add_justify_for_arabic)
    def _set_just_number(self):
        if self.just_number:
            self.textvariable.trace_add('write', self.set_just_number)
        
    
    def set_just_number(self, *k):
        val = self.textvariable.get()
        number = True
        if val:
            if not val[0].isdigit():
                self.textvariable.set(val[1:])
                number = False
            
            elif not val[-1].isdigit():
                self.textvariable.set(val[:-1])
                number = False
                
            if (not number) and self.show_err_callback:
                message = render_text("وارد کردن عدد")
                self.show_err_callback(message)
        
    # Callback to enforce that only English characters can be entered.
    def _set_english_only(self, *k):
        val = self.textvariable.get()
        # Ignore the callback if the text is just the initial placeholder.
        if val == self.placeholder_text:
            return

        arabic = False
        if val:
            # Check if an Arabic character was just added at the beginning or end.
            if isarabic(val[0]):
                self.textvariable.set(val[1:]) # Remove the invalid character.
                arabic = True
            
            elif isarabic(val[-1]):
                self.textvariable.set(val[:-1]) # Remove the invalid character.
                arabic = True
                
            # If an invalid character was removed, show an error message.
            if arabic and self.show_err_callback:
                message = render_text("وارد کردن کاراکتر انگلیسی")
                self.show_err_callback(message)
    
    # Binds the English-only validation callback if the 'just_english' flag is set.
    def _set_just_english(self):
        if self.just_english:
            self.textvariable.trace_add('write', self._set_english_only)
    
    def _set_just_text(self):
        if self.just_text:
            self.textvariable.trace_add('write', self.set_just_text)
    
    def set_just_text(self, *k):
        val = self.textvariable.get()
        
        text = True
        if val:
            # Check if the first or last character is Arabic
            if val[0].isdigit():
                self.textvariable.set(val[1:])
                text = False
            
            elif val[-1].isdigit():
                self.textvariable.set(val[:-1])
                text = False
            
            if not text and self.show_err_callback:
                    message = render_text("وارد کردن کاراکتر")
                    self.show_err_callback(message)
        
    
    def set_placeholder_text(self, text:str):
        if isarabic(text):
            text = render_text(text)
        self.placeholder_text = text
        self.textvariable.set(text)
            
    
    # Custom get() method to handle cases where the placeholder text is still visible.
    def get(self):
        val = self.textvariable.get()
        # If the current text is the placeholder, return an empty string instead.
        if self.placeholder_empty and val == self.placeholder_text:
            return ""
        else:
            return val
    
    def clear(self):
        self.textvariable.set('')
        
 # A simple subclass of CTk to create a root window, with an option for fullscreen.
class Root(CTk):
    def __init__(self, fullscreen=True, **kwargs):
        super().__init__(**kwargs)
        
        # If fullscreen is requested, maximize the window.
        if fullscreen:
            self.win_max()
    
    # A method to set the window geometry to the maximum screen size.
    def win_max(self):
        max_width = self.winfo_screenwidth()
        max_height = self.winfo_screenheight()
        self.geometry('{}x{}+0+0'.format(max_width, max_height))
    
# A highly custom button created using a Canvas to allow for individually rounded corners.
# This class manually draws a polygon and binds mouse events to simulate a button.
class Item_button(CTkCanvas):
    def __init__(self, root, width:int=0, height:int=0, color='#AFB3ED',hover_color="#4e4e61",background="#5B5D76", raduis:int=None, rtopleft:int=0, rtopright:int=0, rbottomleft:int=0, rbottomtright:int=0, **kwargs):
        super().__init__(root,width=width, height=height, background=background, highlightthickness=0)
        self.color=color
        # If a single radius is provided, apply it to all corners.
        if raduis:
            rtopleft, rtopright, rbottomleft, rbottomtright = (raduis, raduis, raduis, raduis)
        
        self.rtopleft = rtopleft
        self.rtopright = rtopright
        self.rbottomleft = rbottomleft
        self.rbottomtright = rbottomtright
        
        self.width = width
        self.height = height
        self.hover_color = hover_color
        # Create the main polygon shape of the button and store its ID.
        self.polygon_id = self.create_rounded_box(0, 0, width, height)
        self._set_hover()
    
    # A static method to generate the points for a 90-degree arc (a rounded corner).
    @staticmethod
    def get_cos_sin(radius: int) -> Iterator[tuple[float, float]]:
        # The number of steps determines the smoothness of the curve.
        steps = max(radius, 10)
        for i in range(steps + 1):
            angle = pi * (i / steps) * 0.5 # Angle ranges from 0 to pi/2 (90 degrees).
            yield (cos(angle) - 1) * radius, (sin(angle) - 1) * radius

    # Creates the polygon shape for the button with the specified corner radii.
    def create_rounded_box(self, x1: int, y1: int, x2: int, y2: int) -> int:
        points = []
        # Get the lists of points that define the curve for each corner.
        TR_angle_point = tuple(Item_button.get_cos_sin(self.rtopright))
        BR_angle_point = tuple(Item_button.get_cos_sin(self.rbottomtright))
        BL_angle_point = tuple(Item_button.get_cos_sin(self.rbottomleft))
        TL_angle_point = tuple(Item_button.get_cos_sin(self.rtopleft))
        
        # Calculate the absolute coordinates for the polygon by combining the corner arcs.
        for cos_r, sin_r in TR_angle_point:
            points.append((x2 + sin_r, y1 - cos_r))         # Top right corner
        for cos_r, sin_r in BR_angle_point:
            points.append((x2 + cos_r, y2 + sin_r))         # Bottom right corner
        for cos_r, sin_r in BL_angle_point:
            points.append((x1 - sin_r, y2 + cos_r))         # Bottom left corner
        for cos_r, sin_r in TL_angle_point:
            points.append((x1 - cos_r, y1 - sin_r))         # Top left corner
        
        # Create the polygon on the canvas using the calculated points.
        return self.create_polygon(points, fill=self.color, smooth=True, joinstyle='round')

    # Creates and centers text on top of the canvas-based button.
    def set_text(self, text:str, fill, font_size):
        if isarabic(text):
            text = render_text(text)
        x = self.width / 2
        y = self.height / 2
        self.create_text(x, y, text = text, fill=fill, font=(None, font_size))
    
    # Manually binds mouse enter/leave events to the canvas to simulate a hover effect.
    def _set_hover(self):
        self.bind("<Enter>", lambda _: self.itemconfig(self.polygon_id, fill=self.hover_color))
        self.bind("<Leave>", lambda _: self.itemconfig(self.polygon_id, fill=self.color))
        
    
    # Binds a click action (mouse button 1) to the canvas widget.
    def set_action(self, action):
        self.bind("<Button-1>", action)
        
# A customized CTkComboBox that provides a consistent, predefined style.
        
class DropDown(CTkComboBox):
    def __init__(self, window, width=140, height=28, dropdown_fg_color='#393A4E', dropdown_text_color="white",button_color="#8889a6", fg_color="#393A4E",text_color="white", border_color="#8889a6", **kwargs):
        
        super().__init__(window, width=width, height=height, dropdown_fg_color=dropdown_fg_color,\
                        dropdown_text_color=dropdown_text_color, text_color=text_color, fg_color=fg_color,\
                        button_color=button_color, corner_radius=15, border_color=border_color, **kwargs)
        
        

# A factory function to create a labeled field with an updatable value.
# It uses a container dictionary to prevent re-creating the widget if called multiple times.
def create_updatable_labels(window, label_name, row, column, field_key, container:dict,font_size=13, **kwargs):
    # Only create the widget if it doesn't already exist in the container.
    if field_key not in container:
        temp_frame = CTkFrame(window, fg_color="#444759", corner_radius=10)
        temp_frame.grid(row=row, column=column, sticky="ew", **kwargs)
        label = CTkLabel(temp_frame, text=label_name, text_color="white", font=(None, font_size))
        label.pack(expand=True, fill="both", padx=10, pady=5, side="right")
        label_val = CTkLabel(temp_frame, text="?", text_color="white", font=(None, font_size))
        label_val.pack(expand=True, fill="both", padx=10, pady=5, side="right")
        # Store the created value label in the container for future access.
        if container is not None:
            container[field_key] = label_val
        return label_val
    # If the widget already exists, return the stored reference from the container.
    return container[field_key]

# A factory function to create a labeled input field.
# It uses a container dictionary to store a reference to the created widget, preventing duplicates.
def create_input_fields(window, label_text, row, column, field_key, container:dict,font_size=13, char_limit = 20,just_english=False,just_number=False,just_text=False, show_err_callback=None, **kwargs):
    # Only create the widget if it doesn't already exist in the container.

    if (container is None) or field_key not in container:
        frame = CTkFrame(window, fg_color="transparent", bg_color="transparent")
        frame.grid(row=row, column=column, sticky="ew", **kwargs)
        label = CTkLabel(frame, text=label_text, text_color="white", font=(None, font_size))
        label.pack(expand=True, fill="both", padx=10, pady=5, side="right")
        var = StringVar()
        input_widget = Input(frame, 15, 150, 35, None, var, placeholder_empty=False, just_english=just_english, just_number=just_number, just_text=just_text,char_limit=char_limit, show_err_callback=show_err_callback)
        input_widget.set_textvariable(var)
        input_widget.pack(expand=True, fill="both", padx=10, pady=5, side="right")
        # Store the created input widget in the container for future access.
        if container is not None:
            container[field_key] = input_widget
        return input_widget
    # If the widget already exists, return the stored reference.
    return container[field_key]