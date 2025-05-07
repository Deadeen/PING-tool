import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import threading
import time
import queue

class PingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ping Monitor")
        self.root.geometry("500x400")
        
        # Make the window resizable
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Variables
        self.ping_results = []
        self.is_pinging = False
        self.start_time = None
        self.message_queue = queue.Queue()
        
        # GUI Elements
        self.create_widgets()
        
        # Start checking the message queue
        self.check_queue()

    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Title label
        self.label = tk.Label(main_frame, text="Ping Monitor", font=("Arial", 16))
        self.label.grid(row=0, column=0, pady=10, sticky="n")

        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=5, sticky="n")

        self.start_button = tk.Button(button_frame, text="Start", command=self.start_pinging)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop", command=self.stop_pinging, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Result text with scrollbar
        text_frame = tk.Frame(main_frame)
        text_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.result_text = tk.Text(text_frame, height=15, width=60, state=tk.DISABLED, 
                                 yscrollcommand=self.scrollbar.set, wrap=tk.WORD)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.result_text.yview)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = tk.Label(main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=3, column=0, sticky="ew")

    def check_queue(self):
        """Check the message queue for updates from the ping thread"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.update_display(message)
        except queue.Empty:
            pass
        
        # Schedule to check again after 100ms
        self.root.after(100, self.check_queue)

    def update_display(self, message):
        """Update the display with a new message"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.see(tk.END)  # Auto-scroll to bottom
        self.result_text.config(state=tk.DISABLED)

    def update_status(self, message):
        """Update the status bar"""
        self.status_var.set(message)

    def start_pinging(self):
        self.is_pinging = True
        self.start_time = time.time()
        self.ping_results = []
        
        # Reset UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        self.update_status("Pinging google.com...")
        self.message_queue.put("Pinging started at " + time.strftime("%H:%M:%S"))
        self.message_queue.put("Pinging google.com...")

        # Start ping in a separate thread
        self.ping_thread = threading.Thread(target=self.ping_google, daemon=True)
        self.ping_thread.start()

    def stop_pinging(self):
        self.is_pinging = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Ready")
        
        # Wait for the ping thread to finish (if it's still running)
        if self.ping_thread.is_alive():
            self.ping_thread.join(timeout=1)
        
        self.display_final_results()

    def ping_google(self):
        ping_count = 0
        
        while self.is_pinging and (time.time() - self.start_time) < 3600:  # Run for 1 hour max
            ping_count += 1
            current_time = time.time() - self.start_time
            
            try:
                # Ping Google (1 packet, 1 second timeout)
                output = subprocess.run(
                    ["ping", "-n", "1", "-w", "1000", "google.com"],  # Windows
                    # ["ping", "-c", "1", "-W", "1", "google.com"],  # Linux/Mac
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                if output.returncode == 0:
                    # Extract ping time from output (Windows format)
                    if "time=" in output.stdout:
                        time_str = output.stdout.split("time=")[1].split(" ")[0]
                        ping_time = float(time_str.replace("ms", ""))
                        self.ping_results.append(ping_time)
                        self.message_queue.put(f"Ping #{ping_count} ({current_time:.1f}s): {ping_time}ms")
                    else:
                        self.ping_results.append(None)
                        self.message_queue.put(f"Ping #{ping_count} ({current_time:.1f}s): Success but no time value")
                else:
                    self.ping_results.append(None)
                    self.message_queue.put(f"Ping #{ping_count} ({current_time:.1f}s): Request timed out")

            except Exception as e:
                self.ping_results.append(None)
                self.message_queue.put(f"Ping #{ping_count} ({current_time:.1f}s): Error - {str(e)}")

            time.sleep(1)  # Wait for 1 second before next ping

        self.is_pinging = False
        self.message_queue.put("Ping stopped at " + time.strftime("%H:%M:%S"))
        self.root.after(100, self.display_final_results)

    def display_final_results(self):
        if not self.ping_results:
            self.message_queue.put("No ping results found.")
            return

        # Calculate statistics
        successful_pings = [ping for ping in self.ping_results if ping is not None]
        lost_connections = self.ping_results.count(None)
        total_pings = len(self.ping_results)

        if successful_pings:
            avg_ping = sum(successful_pings) / len(successful_pings)
            max_ping = max(successful_pings)
            min_ping = min(successful_pings)
        else:
            avg_ping = max_ping = min_ping = "N/A"

        # Display results
        self.message_queue.put("\n=== Final Results ===")
        self.message_queue.put(f"Total pings sent: {total_pings}")
        self.message_queue.put(f"Average Ping: {avg_ping if avg_ping == 'N/A' else f'{avg_ping:.2f} ms'}")
        self.message_queue.put(f"Highest Ping: {max_ping if max_ping == 'N/A' else f'{max_ping} ms'}")
        self.message_queue.put(f"Lowest Ping: {min_ping if min_ping == 'N/A' else f'{min_ping} ms'}")
        self.message_queue.put(f"Packet Loss: {lost_connections}/{total_pings} ({lost_connections/total_pings*100:.1f}%)")

if __name__ == "__main__":
    root = tk.Tk()
    app = PingApp(root)
    root.mainloop()
