import sqlite3


# Connect to db, create if does not exist
def open_connection():   
    conn = sqlite3.connect('local_cache.db')
    c = conn.cursor()
    return (conn,c)

# Create tables
def init(con,cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS leaking
                (id text, ch4 real, long real, lat real, time real)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS target
                (id text, ch4 real, long real, lat real, time real)''')
    con.commit()

# Clear cache
def clear_cache(conn,cur):
    sql = 'DELETE FROM leaking'
    cur.execute(sql)
    conn.commit()
    sql = 'DELETE FROM target'
    cur.execute(sql)
    conn.commit()
    
# Insert to the table
def insert_table(con,cursor,id,ch4,lon,lat,time,name):
    cursor.execute("INSERT INTO "+name+" VALUES ('"+id+"','"+str(ch4)+"','"+str(lon)+"','"+str(lat)+"','"+str(time)+"')")
    # print("affected rows = {}".format(cursor.rowcount))
    con.commit()
    
# Select to the table
def select_table(cursor,time,name):
    t = (time,)
    cursor.execute('SELECT * FROM '+name+' WHERE time>?', t)
    return cursor.fetchone()

# Close the connection
def close_connection(conn):
    conn.close()
