import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import threading
import time

class PingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ping Monitor")
        self.root.geometry("400x300")

        # Variables
        self.ping_results = []
        self.is_pinging = False
        self.start_time = None

        # GUI Elements
        self.label = tk.Label(root, text="Ping Monitor", font=("Arial", 16))
        self.label.pack(pady=10)

        self.start_button = tk.Button(root, text="Start", command=self.start_pinging)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_pinging, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.result_text = tk.Text(root, height=10, width=50, state=tk.DISABLED)
        self.result_text.pack(pady=10)

    def start_pinging(self):
        self.is_pinging = True
        self.start_time = time.time()
        self.ping_results = []
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Pinging started...\n")
        self.result_text.config(state=tk.DISABLED)

        # Start ping in a separate thread
        self.ping_thread = threading.Thread(target=self.ping_google)
        self.ping_thread.start()

    def stop_pinging(self):
        self.is_pinging = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.display_results()

    def ping_google(self):
        while self.is_pinging and (time.time() - self.start_time) < 3600:  # Run for 1 hour
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
                        # Extract the time value (e.g., "time=45ms")
                        time_str = output.stdout.split("time=")[1].split(" ")[0]
                        # Remove "ms" and convert to float
                        ping_time = float(time_str.replace("ms", ""))
                        self.ping_results.append(ping_time)
                    else:
                        # Ping succeeded but no time value (unlikely)
                        self.ping_results.append(None)
                else:
                    # Ping failed (e.g., timeout or unreachable host)
                    self.ping_results.append(None)

            except Exception as e:
                print(f"Error: {e}")
                self.ping_results.append(None)

            time.sleep(1)  # Wait for 1 second before next ping

        self.is_pinging = False
        self.display_results()

    def display_results(self):
        if not self.ping_results:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.insert(tk.END, "No ping results found.\n")
            self.result_text.config(state=tk.DISABLED)
            return

        # Calculate statistics
        successful_pings = [ping for ping in self.ping_results if ping is not None]
        lost_connections = self.ping_results.count(None)

        if successful_pings:
            avg_ping = sum(successful_pings) / len(successful_pings)
            max_ping = max(successful_pings)
            min_ping = min(successful_pings)
        else:
            avg_ping = max_ping = min_ping = "N/A"

        # Find when max, min, and lost connections occurred
        max_index = self.ping_results.index(max_ping) if successful_pings else "N/A"
        min_index = self.ping_results.index(min_ping) if successful_pings else "N/A"
        lost_indices = [i for i, x in enumerate(self.ping_results) if x is None]

        # Display results
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, f"Average Ping: {avg_ping if avg_ping == 'N/A' else f'{avg_ping:.2f} ms'}\n")
        self.result_text.insert(tk.END, f"Highest Ping: {max_ping if max_ping == 'N/A' else f'{max_ping} ms'} (at {max_index} seconds)\n")
        self.result_text.insert(tk.END, f"Lowest Ping: {min_ping if min_ping == 'N/A' else f'{min_ping} ms'} (at {min_index} seconds)\n")
        self.result_text.insert(tk.END, f"Lost Connections: {lost_connections} times\n")
        if lost_indices:
            self.result_text.insert(tk.END, f"Connection lost at: {lost_indices} seconds\n")
        self.result_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = PingApp(root)
    root.mainloop()