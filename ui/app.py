import tkinter as tk
from threading import Thread
import time
from PIL import Image, ImageTk

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Dnd Agent")
        self.root.geometry("1000x800")
        self.root.configure(bg="#60baff")

        self.listen_button = tk.Button(root, text="Проговорить запрос", command=self.start_listen, bg="red", fg="black",
                                       font=("Arial", 20, "bold"))
        self.listen_button.pack(pady=20)

        self.canvas = tk.Canvas(root, width=50, height=50, bg="#60baff", highlightthickness=0)
        self.arc = self.canvas.create_arc(5, 5, 45, 45, start=0, extent=90, outline="#000000", width=4, style=tk.ARC)
        self.canvas.pack_forget()

        self.angle = 0
        self.running = False

        self.image_canvas = tk.Canvas(root, width=300, height=200, bg="#f0f0f0", highlightthickness=0)
        self.image_canvas.pack_forget()

    def start_listen(self):
        self.listen_button.config(text="Отправить запрос", command=self.start_send_request)

        task_thread = Thread(target=self.listen)
        task_thread.start()

    def start_send_request(self):
        self.listen_button.config(text="Проговорить запрос", command=self.start_listen, state=tk.DISABLED)
        self.canvas.pack(pady=20)
        self.running = True
        self.animate_spinner()

        task_thread = Thread(target=self.send_request)
        task_thread.start()

    def animate_spinner(self):
        if self.running:
            self.angle = (self.angle + 10) % 360
            self.canvas.itemconfig(self.arc, start=self.angle)
            self.root.after(50, self.animate_spinner)

    def stop_spinner(self):
        self.running = False
        self.canvas.pack_forget()
        self.listen_button.config(state=tk.NORMAL)

    def listen(self):
        time.sleep(2)

    def send_request(self):
        time.sleep(2)
        self.root.after(0, self.show_image)

    def show_image(self):
        self.stop_spinner()
        image = Image.open("picture.jpg")
        image = image.resize((300, 200))
        self.tk_image = ImageTk.PhotoImage(image)
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.image_canvas.pack(pady=20)



if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
