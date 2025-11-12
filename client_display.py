import client_file_commands
import tkinter as tk
from tkinter import ttk


# using classes to organize different frames easily
# There are two pages: the log-in page and the main page where the user will interact with the server
# https://www.geeksforgeeks.org/python/tkinter-application-to-switch-between-different-page-frames/
# ^highly used as a reference for the base structure
# Maybe no loop? Just make the connection and logout/other commands will disconnect!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

class ServerApp(tk.Tk):
    # initializing app
    def __init__(self, *args, **kwargs):
        # initialize class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Socket Server -- Client-Side App")

        window_frame = tk.Frame(self)
        window_frame.pack(side="top", fill="both", expand=True)
        
        window_frame.grid_rowconfigure(0, weight=1)
        window_frame.grid_columnconfigure(0, weight=1)

        # window size
        self.geometry("800x400")

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
    
    # while loop probably needs to go in here, we cannot keep connecting and disconnecting


class SignIn(tk.Frame):
    # initializing sign in page
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        title = ttk.Label(self, text="Server Sign In", font=("Verdana", 35))
        title.grid(row=0, column=4, padx=10, pady=10)
        
        # entry boxes (Entry type)
        username = tk.StringVar()
        password = tk.StringVar()
        username_entry = ttk.Entry(self, textvariable=username)
        username_entry.grid(row=15, column=10)
        password_entry = ttk.Entry(self, textvariable=password)
        password_entry.grid(row=17, column=10)

        # creating sign in button, which takes you to the client page if valid credentials are entered
        button_signin = ttk.Button(self, text="Sign In", 
                        command = lambda: controller.display_frame(ClientPage))
        button_signin.grid(row=19, column=10, padx=10,pady=10)

    # -----button commands-----
    # method for signing in, which will use server side commands
    # def signin_clicked(self):
    #     print("logged in")


class ClientPage(tk.Frame):
    # initializing client page
    def __init__(self, parent, controller):
        # 
        tk.Frame.__init__(self, parent)
        # window title

        # label
        label = ttk.Label(self, text="Server Files", font=("Verdana", 20))
        label.grid(row=0, column=4, padx=10, pady=10)

        # file display (need a scroll feature and maybe a separate frame displayed here)
        file_box = tk.Listbox(self, height=15, width=80)
        file_box.grid(row=1, column=2, rowspan=4, columnspan=5)
        
        # -----buttons------
        style = ttk.Style()
        style.configure('W.TButton', foreground='red')
        logout_button = ttk.Button(self, text="Log Out", 
                        command = lambda: controller.display_frame(SignIn))
        logout_button.grid(row=15,column=10, padx=10, pady=10)
        dir_button = ttk.Button(self, text="Dir", 
                        command = None)
        dir_button.grid(row=14, column=1, padx=10, pady=10)
        upload_button = ttk.Button(self, text="Upload", 
                        command = None)
        upload_button.grid(row=15, column=1, padx=10, pady=10)
        download_button = ttk.Button(self, text="Download", 
                        command = None)
        download_button.grid(row=15, column=2, padx=10, pady=10)
        new_button = ttk.Button(self, text="New Directory", 
                        command=None)
        new_button.grid(row=15, column=3, padx=10, pady=10)
        delete_button = ttk.Button(self, text="Delete", style='W.TButton', 
                        command=None)
        
        delete_button.grid(row=15, column=4, padx=10, pady=10)

    # -----button commands-----
    def fetch_files(self):
        # for loop for inserting files from server
        print("hiiiii")

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
