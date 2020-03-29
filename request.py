import requests
import json
import requests_cache
import time
from IPython.core.display import clear_output
import pandas as pd
from tqdm import tqdm

API_KEY = '438910b297376c62655e6041f73f2684'
USER_AGENT = 'Dataquest'

def lastfm_get(payload):
    # define headers and URL
    headers = {'user-agent': USER_AGENT}
    url = 'http://ws.audioscrobbler.com/2.0/'

    # Add API key and format to the payload
    payload['api_key'] = API_KEY
    payload['format'] = 'json'

    response = requests.get(url, headers=headers, params=payload)
    return response

def jprint(obj):
    # create a formatted string of the Python JSON object
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def lookup_tags(artist):
    response = lastfm_get({
        'method': 'artist.getTopTags',
        'artist':  artist
    })

    # if there's an error, just return nothing
    if response.status_code != 200:
        return None

    # extract the top three tags and turn them into a string
    tags = [t['name'] for t in response.json()['toptags']['tag'][:3]]
    tags_str = ', '.join(tags)

    # rate limiting
    if not getattr(response, 'from_cache', False):
        time.sleep(0.25)
    return tags_str

def main():
    tqdm.pandas()

    responses = []

    page = 1
    total_pages = 99999 # this is just a dummy number so the loop starts

    while page <= 1:
        payload = {
            'method': 'chart.gettopartists',
            'limit': 500,
            'page': page
        }

        # print some output so we can see the status
        print("Requesting page {}/{}".format(page, total_pages))
        # clear the output to make things neater
        clear_output(wait = True)

        # make the API call
        response = lastfm_get(payload)

        # if we get an error, print the response and halt the loop
        if response.status_code != 200:
            print(response.text)
            break

        # extract pagination info
        page = int(response.json()['artists']['@attr']['page'])
        total_pages = int(response.json()['artists']['@attr']['totalPages'])

        # append response
        responses.append(response)

        # if it's not a cached result, sleep
        if not getattr(response, 'from_cache', False):
            time.sleep(0.25)

        # increment the page number
        page += 1

        #jprint(response.json())

    r0 = responses[0]
    r0_json = r0.json()
    r0_artists = r0_json['artists']['artist']
    r0_df = pd.DataFrame(r0_artists)
    r0_df.head()
    

    frames = [pd.DataFrame(r.json()['artists']['artist']) for r in responses]
    artists = pd.concat(frames)

    artists = artists.drop('image', axis=1)
    artists = artists.drop_duplicates().reset_index(drop=True)
    #artists['tags'] = artists['name'].progress_apply(lookup_tags)
    artists[["playcount", "listeners"]] = artists[["playcount", "listeners"]].astype(int)
    artists = artists.sort_values("listeners", ascending=False)

    print(artists.head(10))
    #convert the list to a csv file
    #artists.to_csv('artists.csv', index=False)

    

if __name__ == "__main__":
    main()



