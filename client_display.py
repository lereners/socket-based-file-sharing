from client_file_commands import *
from client import *
from client import serv_response
import socket
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog


# using classes to organize different frames easily
# There are two pages: the log-in page and the main page where the user will interact with the server
# https://www.geeksforgeeks.org/python/tkinter-application-to-switch-between-different-page-frames/
# ^highly used as a reference for the base structure
# Maybe no loop? Just make the connection and logout/other commands will disconnect!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

LOGIN = False

serv_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

def connect(serv_client):
    serv_client.connect(ADDR)
    data = serv_client.recv(SIZE).decode(FORMAT)
    LOGIN = True
    handle_response(data)

def disconnect(serv_client):

    print("Disconnected from the server.")
    serv_client.close() ## close the connection
    
def complete_command(data):
    split = data.split(" ")                     # delimiting w/ space is not ideal, esp if user provides path w/ spaces -> file won't be found
    cmd = split[0].upper()
    arg1 = split[1] if len(split) > 1 else None # first argument, if provided
    arg2 = split[2] if len(split) > 2 else None # second argument, if provided
    process_command(cmd, serv_client, split, arg1, arg2)

class ServerApp(tk.Tk):
    # initializing app
    def __init__(self, *args, **kwargs):
        # initialize class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Socket Server -- serv_client-Side App")

        window_frame = tk.Frame(self)
        window_frame.pack(side="top", fill="both", expand=True)
        
        window_frame.grid_rowconfigure(0, weight=1)
        window_frame.grid_columnconfigure(0, weight=1)

        # window size
        self.geometry("800x450")

        # an array for the two frames
        self.frames = {}

        for frame in (SignIn, serv_clientPage):
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

        # creating sign in button, which takes you to the serv_client page if valid credentials are entered
        button_signin = ttk.Button(self, text="Sign In", 
                        command = lambda: [controller.display_frame(serv_clientPage), connect(serv_client)])
        
        # make new function for authentication, also new button for register below sign in
        # display message saying that sign in and register uses same input boxes
        button_signin.grid(row=19, column=10, padx=10,pady=10)
        # will be [controller.display_frame(serv_clientPage), process_command()]
        # with the password and username
    # -----button commands-----
    # method for signing in, which will use server side commands
    # def signin_clicked(self):
    #     print("logged in")


class serv_clientPage(tk.Frame):
    # initializing serv_client page
    def __init__(self, parent, controller):
        # 
        tk.Frame.__init__(self, parent)
        # window title

        # label
        label = ttk.Label(self, text="Server Files", font=("Verdana", 20))
        label.grid(row=0, column=4, padx=10, pady=10)

        # file display (need a scroll feature and maybe a separate frame displayed here)
        # file_canvas = tk.Canvas(self, bg='blue')
        # file_canvas.grid(row=0, column=0, columnspan=15, sticky='news')
        
        file_box = tk.Listbox(self, height=15, width=80)
        file_box.grid(row=1, column=2, rowspan=4, columnspan=5)
            

        file_name = tk.StringVar()
        file_entry = tk.Entry(self, textvariable=file_name, width = 30)
        file_entry.grid(row=13, column=2)

        device_button = ttk.Button(self, text="From Device", command=lambda : self.get_path(file_entry, file_name))
        device_button.grid(row=13, column=3)

        clearbox_button = ttk.Button(self, text="Clear Entry", command=lambda : self.clear_entrybox(file_entry, file_name))
        clearbox_button.grid(row=13, column=4)

        # event
        file_box.bind('<<ListboxSelect>>', lambda event: self.select_from_list(event, file_entry))

        # -----buttons------
        style = ttk.Style()
        style.configure('W.TButton', foreground='red')
        logout_button = ttk.Button(self, text="Log Out", 
                        command = lambda: [controller.display_frame(SignIn), complete_command("LOGOUT"), disconnect(serv_client)])
        logout_button.grid(row=15,column=10, padx=10, pady=10)
        dir_button = ttk.Button(self, text="Dir", 
                        command = lambda : self.dir_clicked(file_name, file_box))
        dir_button.grid(row=14, column=1, padx=10, pady=10)
        upload_button = ttk.Button(self, text="Upload", 
                        command = lambda: complete_command("UPLOAD " + file_name.get()))
        upload_button.grid(row=15, column=1, padx=10, pady=10)
        download_button = ttk.Button(self, text="Download", 
                        command = lambda : complete_command("DOWNLOAD " + file_name.get()))
        download_button.grid(row=15, column=2, padx=10, pady=10)
        new_button = ttk.Button(self, text="Create Subfolder", 
                        command= lambda : complete_command("SUBFOLDER CREATE " + file_name.get()))
        new_button.grid(row=15, column=3, padx=10, pady=10)
        newdelete_button = ttk.Button(self, text="Delete Subfolder", style='W.TButton',
                        command= lambda : complete_command("SUBFOLDER DELETE " + file_name.get()))
        newdelete_button.grid(row=15, column=4, padx=10, pady=10)
        delete_button = ttk.Button(self, text="Delete File", style='W.TButton', 
                        command=lambda : complete_command("DELETE " + file_name.get()))
        delete_button.grid(row=15, column=5, padx=10, pady=10)

    # -----button commands-----
    def dir_clicked(self, file_name, file_box):
        # for loop for inserting files from server
        # check for if there is a filename listed
        data = "DIR " + file_name.get()
        print(data)
        complete_command(data)
        list_files = return_servresponse().split()
        print(list_files[0])

        file_box.delete(0, tk.END)
        for name in list_files:
            file_box.insert(tk.END, name)

        file_box.grid(row=1, column=2, rowspan=4, columnspan=5)

    def get_path(self, file_entry, file_name):
        # for selecting from device
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = file_path
            print(f"{file_name} was selected.")
            file_entry.insert(0, file_path + " ")

    def clear_entrybox(self, file_entry, file_name):
        # clears the entry box
        file_name = ""
        file_entry.delete(0, tk.END)

    def select_from_list(self, event, file_entry):
        #puts the name of the file selected into the listbox
        widg = event.widget
        ind = int(widg.curselection()[0])
        name = widg.get(ind)
        if name:
            file_entry.delete(0, tk.END)
            file_entry.insert(0, name + " ")
        else:
            print("No file selected")
        


# running the file
def main():
    app = ServerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
