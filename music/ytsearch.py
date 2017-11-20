import discord
from bs4 import BeautifulSoup


async def ytsearch(bot, message, song_name):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}

    async with bot.session.get('https://youtube.com/results',
                                            headers=headers,
                                            params={'search_query': song_name.replace(' ', '+')}) as r:
        html = await r.text()

    soup = BeautifulSoup(html, 'lxml')
    info = [(x.text, "https://youtube.com"+x['href'])
            for x in soup.find_all('a', {'class': 'yt-uix-tile-link '
                                                  'yt-ui-ellipsis yt-ui-ellipsis-2 yt-uix-sessionlink spf-link '})]
    output = []
    for a, b in enumerate(info[:4], 1):
        output.append('{}. {}'.format(a, b[0]))
    outputlist = '\n'.join(map(str, output))
    outputlist = '```py\n' + outputlist + '\n' + '#Choose the appropriate result number or type exit to leave the ' \
                                                 'menu\n' + '``` '
    sent_msg = await message.channel.send(outputlist, delete_after=None)

    def check(m):
        return m.author == message.author and m.channel == message.channel

    while True:
        response_msg = await bot.wait_for('message', check=check, timeout=30)
        if response_msg.content.lower() == 'exit':
            await sent_msg.delete()
            return
        try:
            chosen_number = int(response_msg.content) - 1
            chosen_song = info[chosen_number]
            break
        except KeyError:
            em = discord.Embed(title=':exclamation: Invalid choice', colour=0xff3a38)
            await message.channel.send(embed=em)
    await sent_msg.delete()
    return chosen_song
