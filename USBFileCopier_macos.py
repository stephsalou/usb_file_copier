import stat
import os
import shutil
import subprocess
import time
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox
from tkinter.ttk import Progressbar
from tqdm import tqdm

"""
The USBFileCopier class is a GUI application that allows users to select a source folder and copy its files to connected USB drives. It also provides the option to rename the USB drives and set the copied files as read-only.
Example Usage
# Create an instance of the USBFileCopier class
root = Tk()
usb_copier = USBFileCopier(root)
root.mainloop()
Code Analysis
Main functionalities
Allows users to select a source folder and browse for it using a file dialog.
Copies files from the selected source folder to connected USB drives.
Renames the USB drives with a specified name.
Sets the copied files on the USB drives as read-only.
 
Methods
__init__(self, master): Initializes the USBFileCopier class and creates the GUI elements.
browse_source(self): Opens a file dialog to select the source folder and updates the source entry field.
copy_files(self): Copies files from the source folder to connected USB drives, renames the USB drives, and sets the copied files as read-only.
detect_usb_drives(self): Detects the connected USB drives by running the diskutil list command and parsing the output.
copy_files_to_usb(self, source_folder, new_name, usb_drives): Copies files from the source folder to each USB drive using the shutil.copy function. Displays a progress bar using the tqdm library.
rename_usb_drives(self, usb_drives, new_name): Renames each USB drive using the diskutil rename command.
set_files_read_only(self, usb_drives): Sets the copied files on the USB drives as read-only by changing the file permissions.
 
Fields
master: The root Tkinter window.
source_label: A label for the source folder entry field.
source_entry: An entry field to display the selected source folder.
source_browse_button: A button to open the file dialog for selecting the source folder.
name_label: A label for the new name entry field for USB drives.
name_entry: An entry field to specify the new name for USB drives.
copy_button: A button to initiate the file copying process.
progress_label: A label to display the progress of the file copying process.
progress: A progress bar to visualize the file copying progress.
"""
class USBFileCopier:
    def __init__(self, master):
        self.master = master
        master.title("USB File Copier")

        self.source_label = Label(master, text="Source Folder:")
        self.source_label.grid(row=0, column=0, sticky="w")

        self.source_entry = Entry(master, width=50)
        self.source_entry.grid(row=0, column=1, padx=10, pady=5)

        self.source_browse_button = Button(master, text="Browse", command=self.browse_source)
        self.source_browse_button.grid(row=0, column=2, padx=5, pady=5)

        self.name_label = Label(master, text="New Name for USB Drives:")
        self.name_label.grid(row=2, column=0, sticky="w")

        self.name_entry = Entry(master, width=50)
        self.name_entry.grid(row=2, column=1, padx=10, pady=5)

        self.copy_button = Button(master, text="Copy Files", command=self.copy_files)
        self.copy_button.grid(row=3, columnspan=3, pady=10)

        self.progress_label = Label(master, text="Progress:")
        self.progress_label.grid(row=4, column=0, sticky="w")

        self.progress = Progressbar(master, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=4, column=1, columnspan=2, pady=5)

    def browse_source(self):
        source_folder = filedialog.askdirectory()
        if source_folder:
            self.source_entry.delete(0, "end")
            self.source_entry.insert(0, source_folder)

    def copy_files(self):
        source_folder = self.source_entry.get()
        new_name = self.name_entry.get()

        if not source_folder or not new_name:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        usb_drives = self.detect_usb_drives()
        if usb_drives:
            self.copy_files_to_usb(source_folder, new_name, usb_drives)
            self.rename_usb_drives(usb_drives, new_name)
            self.set_files_read_only(usb_drives,new_name)
            messagebox.showinfo("Success", "Files copied to USB drives and USB drives renamed successfully.")
        else:
            messagebox.showinfo("No USB drives detected.", "No USB drives were detected.")

    def detect_usb_drives(self):
        usb_drives = []
        try:
            diskutil_list = subprocess.Popen(["diskutil", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = diskutil_list.communicate()
            lines = stdout.split("\n")
            for line in lines:
                if "/dev/disk" in line and "external" in line.lower():
                    parts = line.split()
                    usb_drives.append(parts[5])
        except Exception as e:
            print(f"Error detecting USB drives: {e}")
        return usb_drives

    def copy_files_to_usb(self, source_folder, new_name, usb_drives):
        max_retries = 3
        for usb_drive in usb_drives:
            destination_folder = os.path.join(usb_drive, new_name)
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)
            with os.scandir(source_folder) as entries:
                files_to_copy = [entry.name for entry in entries if entry.is_file()]
            with tqdm(total=len(files_to_copy), desc=f"Copying files to {usb_drive}", unit="file") as pbar:
                for file_name in files_to_copy:
                    source_file_path = os.path.join(source_folder, file_name)
                    if os.path.isfile(source_file_path):
                        retry_count = 0
                        while retry_count < max_retries:
                            try:
                                shutil.copy(source_file_path, destination_folder)
                                break
                            except Exception as e:
                                print(f"Error copying file '{file_name}' to {usb_drive}. Retrying...")
                                time.sleep(1)  # Wait 1 sec and retry if somethings wrong
                                retry_count += 1
                        else:
                            print(f"Failed to copy file '{file_name}' to {usb_drive} after {max_retries} attempts.")
                            break
                        pbar.update(1)

    def rename_usb_drives(self, usb_drives, new_name):
        for index, usb_drive in enumerate(usb_drives):
            new_drive_name = f"{new_name}_{index + 1}"
            subprocess.run(["diskutil", "rename", usb_drive, new_drive_name])

    def set_files_read_only(self, usb_drives, new_name):
        for usb_drive in usb_drives:
            copied_folder = os.path.join(usb_drive, new_name)
            for root, dirs, files in os.walk(copied_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    os.chmod(file_path, stat.S_IREAD)


root = Tk()
usb_copier = USBFileCopier(root)
root.mainloop()
