@app.route('/check_db')
def check_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute("PRAGMA table_info(videos)")
    columns = cursor.fetchall()
    
    # Get all videos
    cursor.execute("SELECT * FROM videos")
    videos = cursor.fetchall()
    
    conn.close()
    
    output = "<h2>Videos Table Structure:</h2>"
    output += "<ul>"
    for col in columns:
        output += f"<li>{col}</li>"
    output += "</ul>"
    
    output += f"<h2>Total Videos: {len(videos)}</h2>"
    output += "<ul>"
    for video in videos:
        output += f"<li>{dict(video)}</li>"
    output += "</ul>"
    
    return output