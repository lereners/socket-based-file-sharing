import client_file_commands
import tkinter as tk
from tkinter import ttk


# using classes to organize different frames easily
# There are two pages: the log-in page and the main page where the user will interact with the server
# https://www.geeksforgeeks.org/python/tkinter-application-to-switch-between-different-page-frames/
# ^highly used as a reference for the base structure

class ServerApp(tk.Tk):
    # initializing app
    def __init__(self, *args, **kwargs):
        # initialize class Tk
        tk.Tk.__init__(self, *args, **kwargs)

        window_frame = tk.Frame(self)
        window_frame.pack(side="top", fill="both", expand=True)

        window_frame.grid_rowconfigure(0, weight=1)
        window_frame.grid_columnconfigure(0, weight=1)

        # window size
        self.geometry("725x750")

        # an array for the two frames
        self.frames = {}

        for frame in (SignIn, ClientPage):
            # adding the different frames into the array
            current_frame = frame(window_frame, self)
            self.frames[frame] = current_frame
            current_frame.grid(row=0, column=0, sticky="nsew")

        # display sign in page
        self.display_frame(SignIn)

    # method for displaying frames in the app
    def display_frame(self, frame):
        current_frame = self.frames[frame]
        current_frame.tkraise()


class SignIn(tk.Frame):
    # initializing sign in page
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        title = ttk.Label(self, text="Server Sign In", font=("Verdana", 35))
        title.grid(row=0, column=4, padx=10, pady=10)
        
        # entry boxes (Entry type)
        # username = ""
        # username_entry = ttk.Entry(textvariable=username)
        # username_entry.grid(row=1, column=2, padx=10, pady=10)

        # creating sign in button, which takes you to the client page if valid credentials are entered
        button_signin = ttk.Button(self, text="Sign In", 
                        command = lambda: controller.display_frame(ClientPage))
        button_signin.grid(row=3, column=2, padx=10,pady=10)

    # method for signing in, which will use server side commands
    # def login_clicked(self):
    #     print("logged in")


class ClientPage(tk.Frame):
    # initializing client page
    def __init__(self, parent, controller):
        # 
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="Server Files", font=("Verdana", 35))
        label.grid(row=0, column=4, padx=10, pady=10)

        # file display (need a scroll feature and maybe a separate frame displayed here)

        # buttons

    # definitions for what the buttons actually do????
    # maybe add a log out button
    # use a listbox to display files
    # def display_files(self):
    #     # populate listbox with the file names
    #     print("diplayed")





# running the file
def main():
    app = ServerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
