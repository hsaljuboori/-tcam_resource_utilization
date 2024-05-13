import paramiko
import re
import webbrowser
from datetime import datetime

def ssh_nexus(ip_address, username, password):
    # SSH into the Nexus switch
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip_address, username=username, password=password, look_for_keys=False, allow_agent=False)
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your credentials.")
        return None
    except paramiko.SSHException as e:
        print(f"SSH connection error: {e}")
        return None

    # Send command to retrieve TCAM utilization
    stdin, stdout, stderr = ssh.exec_command("show hardware access-list resource utilization | i 'Protocol CAM'")
    output = stdout.read().decode()

    # Print raw output
    print(f"Raw output from {ip_address}:\n{output}")

    # Close SSH connection
    ssh.close()

    return output

def parse_tcam_utilization(output):
    # Parse the output and extract TCAM utilization
    utilization = re.findall(r'Protocol CAM\s+(\d+)\s+(\d+)\s+([\d.]+)', output)
    if utilization:
        return utilization
    else:
        return None

def create_html_table(utilization, threshold=75):
    # Create HTML table from TCAM utilization data
    html = "<html><head><title>TCAM Utilization</title></head><body>"
    html += "<h2>TCAM Utilization</h2>"
    html += "<table border='1'><tr><th>Switch IP</th><th>Instance</th><th>Entries Used</th><th>Utilization (%)</th></tr>"
    for entry in utilization:
        ip_address, instance, entries, percentage = entry
        color = "black"
        if float(percentage) > threshold:
            color = "red"
        html += f"<tr><td>{ip_address}</td><td>{instance}</td><td>{entries}</td><td style='color:{color}'>{percentage}</td></tr>"
    html += "</table></body></html>"
    return html

# SSH settings
hosts = [
    {'ip_address': '192.168.86.30', 'username': 'admin', 'password': 'xxxxxxxx'},
    {'ip_address': '192.168.86.31', 'username': 'admin', 'password': 'xxxxxxxx'}
]

combined_utilization = []

for host in hosts:
    print(f"Retrieving TCAM utilization from {host['ip_address']}...")
    output = ssh_nexus(host['ip_address'], host['username'], host['password'])
    utilization = parse_tcam_utilization(output)

    if utilization:
        # Add the IP address to each tuple for identification
        for util in utilization:
            combined_utilization.append((host['ip_address'],) + util)
    else:
        print(f"Failed to retrieve TCAM utilization from {host['ip_address']}.")

# Create HTML table
if combined_utilization:
    html_table = create_html_table(combined_utilization)
    filename = f"TCAM_Utilization_Combined_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.html"
    with open(filename, "w") as file:
        file.write(html_table)
    print(f"HTML output saved to {filename}")

    # Open the HTML file in the default web browser
    webbrowser.open(filename)
else:
    print("No TCAM utilization data retrieved.")

