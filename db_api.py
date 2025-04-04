from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

ENGINE = create_engine('sqlite:///./DB/data.db',
                       connect_args={'check_same_thread': False})
Session = sessionmaker(bind=ENGINE)


def create_link_record(tg_user_id,long_link,short_link,created_at):
    s = Session()
    sql_text = text("""
        INSERT INTO links (tg_user_id, long_link, short_link, created_at)
        VALUES (:tg_user_id, :long_link, :short_link, :created_at)
    """)
    params = {
        "tg_user_id": tg_user_id,
        "long_link": long_link,
        "short_link": short_link,
        "created_at": created_at
    }
    s.execute(sql_text, params)
    s.commit()

def get_links(limit=10,offset=0):
    s = Session()
    sql_text = text('SELECT id, short_link FROM links LIMIT :limit OFFSET :offset')
    rows = s.execute(sql_text, params={'limit': limit, 'offset': offset}).fetchall()
    return rows

def update_link_clicks(short_link,clicks):
    s = Session()
    sql_text = text('UPDATE links SET clicks= :clicks WHERE short_link= :short_link')
    s.execute(sql_text, params={'clicks': clicks, 'short_link': short_link})
    s.commit()

def get_top_links(tg_user_id, created_after=0,limit=10):
    s = Session()
    sql_text = text("""
        SELECT short_link, clicks 
        FROM links 
        WHERE tg_user_id= :tg_user_id AND created_at > :created_after 
        ORDER BY clicks 
        LIMIT :limit
    """)
    rows = s.execute(sql_text,  params={'tg_user_id': tg_user_id, 'created_after': created_after, 'limit': limit}).fetchall()
    return rows