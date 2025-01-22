import sqlite3

# Connect to the database
conn = sqlite3.connect('/workspaces/blank-pidapp-1/pid_labeling_tool.db')
cursor = conn.cursor()

# Query the projects table
cursor.execute("SELECT * FROM projects")
rows = cursor.fetchall()

# Print the results
for row in rows:
    print(row)

# Close the connection
conn.close()