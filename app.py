import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from client import FileClient
from server import FileServer
import threading

class App:
    def __init__(self, root):
        self.root = root
        self.server = FileServer('0.0.0.0', 8000)
        self.client = FileClient('127.0.0.1', 8000)

        self.root.title("File Transfer & LNS")
        self.root.geometry("700x500")
        self.root.configure(bg="#f0f0f0")

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat",
                             background="#ccc", font=("Helvetica", 12))
        self.style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 12))

        self.create_widgets()

        threading.Thread(target=self.server.start_server, daemon=True).start()

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.upload_button = ttk.Button(self.main_frame, text="Upload File", command=self.upload_file)
        self.upload_button.grid(column=0, row=0, pady=10, sticky=tk.W)

        self.download_button = ttk.Button(self.main_frame, text="Download File", command=self.download_file)
        self.download_button.grid(column=1, row=0, pady=10, sticky=tk.W)

        self.list_button = ttk.Button(self.main_frame, text="List Server Files", command=self.list_files)
        self.list_button.grid(column=2, row=0, pady=10, sticky=tk.W)

        self.register_button = ttk.Button(self.main_frame, text="Register User", command=self.register_user)
        self.register_button.grid(column=0, row=1, pady=10, sticky=tk.W)

        self.retrieve_button = ttk.Button(self.main_frame, text="Retrieve User", command=self.retrieve_user)
        self.retrieve_button.grid(column=1, row=1, pady=10, sticky=tk.W)

        self.sync_button = ttk.Button(self.main_frame, text="Sync LNS", command=self.sync_lns)
        self.sync_button.grid(column=2, row=1, pady=10, sticky=tk.W)

        self.contacts_button = ttk.Button(self.main_frame, text="View Contacts", command=self.view_contacts)
        self.contacts_button.grid(column=1, row=2, pady=10, sticky=tk.W)

        self.quit_button = ttk.Button(self.main_frame, text="Quit", command=self.root.quit)
        self.quit_button.grid(column=1, row=3, pady=10, sticky=tk.W)

        for child in self.main_frame.winfo_children():
            child.grid_configure(padx=10, pady=5)

    def upload_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.client.upload_file(filename)
            messagebox.showinfo("Success", f"File {filename} uploaded successfully")

    def download_file(self):
        filename = filedialog.askstring("Download File", "Enter filename to download:")
        if filename:
            self.client.download_file(filename)
            messagebox.showinfo("Success", f"File {filename} downloaded successfully")

    def list_files(self):
        files = self.client.list_files()
        files_str = "\n".join(files)
        messagebox.showinfo("Server Files", files_str)

    def register_user(self):
        register_window = tk.Toplevel(self.root)
        register_window.title("Register User")
        register_window.geometry("400x300")
        register_window.configure(bg="#f0f0f0")

        ttk.Label(register_window, text="Username:").grid(column=0, row=0, padx=10, pady=10, sticky=tk.W)
        username_entry = ttk.Entry(register_window)
        username_entry.grid(column=1, row=0, padx=10, pady=10)

        ttk.Label(register_window, text="Date of Birth (YYYY-MM-DD):").grid(column=0, row=1, padx=10, pady=10, sticky=tk.W)
        dob_entry = ttk.Entry(register_window)
        dob_entry.grid(column=1, row=1, padx=10, pady=10)

        ttk.Label(register_window, text="Full Name:").grid(column=0, row=2, padx=10, pady=10, sticky=tk.W)
        full_name_entry = ttk.Entry(register_window)
        full_name_entry.grid(column=1, row=2, padx=10, pady=10)

        def submit():
            user_data = {
                "username": username_entry.get(),
                "dob": dob_entry.get(),
                "full_name": full_name_entry.get()
            }
            self.client.register_user(user_data)
            register_window.destroy()
            messagebox.showinfo("Success", f"User {user_data['username']} registered successfully")

        submit_button = ttk.Button(register_window, text="Submit", command=submit)
        submit_button.grid(column=1, row=3, pady=10)

        for child in register_window.winfo_children():
            child.grid_configure(padx=10, pady=5)

    def retrieve_user(self):
        username = filedialog.askstring("Retrieve User", "Enter username to retrieve:")
        if username:
            self.client.retrieve_user(username)
            messagebox.showinfo("Success", f"User {username} retrieved successfully")

    def sync_lns(self):
        self.client.sync_lns()
        messagebox.showinfo("Success", "LNS sync successful")

    def view_contacts(self):
        contacts_window = tk.Toplevel(self.root)
        contacts_window.title("Contacts")
        contacts_window.geometry("400x300")
        contacts_window.configure(bg="#f0f0f0")

        contacts = self.client.get_local_lns()
        contacts_str = "\n".join(f"{username}: {user_id}" for username, user_id in contacts.items())

        contacts_label = ttk.Label(contacts_window, text=contacts_str)
        contacts_label.grid(column=0, row=0, padx=10, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
