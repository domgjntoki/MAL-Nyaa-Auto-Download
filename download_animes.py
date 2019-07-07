import os
import requests
from bs4 import BeautifulSoup
import threading
import re

# -=-=-= User info =-=-=-
mal_username = 'Username' # input('My anime List username: ')
download_dir = 'C:\\Users\\User\\Downloads\\' # input('Download Dir: ')
# -=-=-=-=-=-=-=-=-=-=-=-=

print(f"Searching {mal_username}'s wathing list...")
mal_watching_list = requests.get(f'https://api.jikan.moe/v3/user/'
                                 f'{mal_username}/animelist/watching').json()['anime']
print('Searching your animes in Nyaa.si...\n')

# search for animes, limit for search 4 at same time (avoids getting kicked)
max_threads = 4
sema = threading.Semaphore(value=max_threads)
downloaded = os.listdir(download_dir) # Avoids re-downloading

# Add your patterns here
erai_pattern = re.compile('\\[Erai-raws\\] (.+) - (\d+)')
arukoru_pattern = re.compile('\\[Arukoru\\] (.+) - Episode (\d+)')
horrible_pattern = re.compile('\\[HorribleSubs\\] (.+) - (\d+)')
hakata_ramen_pattern = re.compile('\\[Hakata Ramen\\] (.+) (\d+)')
    
def download_unseen_episodes(mal_anime):
    sema.acquire()
    query = mal_anime['title']
    url = f'https://nyaa.si/?f=0&c=1_2&q={query}&p=1'
    site = requests.get(f'https://nyaa.si/?f=0&c=1_2&q={query}&p=1')
    soup = BeautifulSoup(site.content, 'html.parser')
    try:
        table = soup.select('table[class="table table-bordered table-hover table-striped torrent-list"]')[0]
    except IndexError:
        print(f'error in "{query}", check that shit')
        return
    
    animes_downloaded = []
    subs = []
    rows = table.find_all('tr')[1:]
    anime_title = mal_anime['title']
    for row in rows:
        elements = row.find_all('td')
        title = elements[1].select('a')
        title = title[0] if len(title) == 1 else title[1]
        title = title.get('title')
        magnet = elements[2].select_one('a[href^=magnet]').get('href')
        if erai_pattern.match(title):
            ep = erai_pattern.match(title).groups()[1]
            sub = 'Erai-raws'
        elif arukoru_pattern.match(title):
            ep = arukoru_pattern.match(title).groups()[1]
            sub = 'Arukoru'
        elif horrible_pattern.match(title):
            ep = horrible_pattern.match(title).groups()[1]
            sub = 'HorribleSubs'
        elif hakata_ramen_pattern.match(title):
            ep = hakata_ramen_pattern.match(title).groups()[1]
            sub = 'Hakata Ramen'
        else:
            continue

        if int(ep) > mal_anime['watched_episodes'] and (
                (anime_title, ep) not in animes_downloaded):
            # Starts magnet link if it's not already downloaded
            if title not in downloaded:
                os.startfile(magnet)
            animes_downloaded.append((anime_title, ep))
            subs.append(sub)
    print(f'Search Completed: {query}\n'
          f'Downloaded Episodes: {animes_downloaded}, subs={subs}\n')
    sema.release()


threads = [threading.Thread(target=download_unseen_episodes,
           args=[mal_anime])
           for mal_anime in mal_watching_list]
[thread.start() for thread in threads]
[thread.join() for thread in threads]
print('All animes were searched.')
