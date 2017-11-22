async def fetch_user(conn, user_id):

    user_row = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)

    if user_row is not None:
        return user_row
    else:
        return await add_user(conn, user_id)


async def add_user(conn, user_id):

    async with conn.transaction():
        await conn.execute('INSERT INTO users VALUES($1)', user_id)
        user_row = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)

    return user_row
