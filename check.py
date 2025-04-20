import requests
from atproto import Client, client_utils, models
from mastodon import Mastodon
from bs4 import BeautifulSoup

with open("mastodonkeys.txt") as f:
    lines = f.readlines()
    MASTODON_ACCESS_TOKEN, = [l.strip() for l in lines]
with open("bluesky.txt") as f:
    blueskykey = f.read().strip()

text = "Current #IceOut conditions in #AlgonquinPark. Image courtesy of The Friends of Algonquin Park. https://www.algonquinpark.on.ca/news/ice-out.php"
alt = "A webcam shot of Lake of Two Rivers in Algonquin Park."

try:
    URL = "https://www.algonquinpark.on.ca/news/ice-out.php"
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    content_center = soup.find(id="content_center")

    second_div = content_center.find_all('div', recursive=False)[1]  # Remember Python uses 0-based indexing
    first_a = second_div.find('a')
    link = first_a.get('href')
    link = "https://www.algonquinpark.on.ca/images_ice/images_ice/" + link.split("/")[-1]
except Exception as e:
    print(f"Error getting link: {e}")


try:
    response = requests.get(link, stream=True)
    response.raise_for_status()  # Raise an exception for bad status codes

    with open("iceout.jpg", 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    print(f"Image downloaded successfully.")
except requests.exceptions.RequestException as e:
    print(f"Error downloading image: {e}")
except IOError as e:
    print(f"Error saving image to path: {e}")

try:
    mastodon = Mastodon(
            access_token = MASTODON_ACCESS_TOKEN,
            api_base_url = "https://mastodon.social/",
            )
except:
    print("Error accessing mastodon.")

try:
    media = mastodon.media_post("iceout.jpg", description=alt)
    print(f"Image uploaded successfully. Media ID: {media['id']}")
    
    mastodon.status_post(alt, media_ids=[media['id']])
    print("Toot with image posted successfully!")
except Exception as e:
    print(f"Error uploading media: {e}")

try:
    client = Client()
    client.login('iceoutbot.bsky.social', blueskykey)

    with open("iceout.jpg", 'rb') as image_file:
        image_bytes = image_file.read()

    aspect_ratio = models.AppBskyEmbedDefs.AspectRatio(height=810, width=1440)

    text_builder = client_utils.TextBuilder()
    text_builder.text("Current ")
    text_builder.tag("#IceOut", "IceOut")
    text_builder.text(" conditions in ")
    text_builder.tag("Algonquin Park", "AlgonquinPark")
    text_builder.text(". Image courtesy of ")
    text_builder.link("The Friends of Algonquin Park", "https://www.algonquinpark.on.ca/news/ice-out.php")
    text_builder.text(".")

    client.send_image(
        text=text_builder,
        image=image_bytes,
        image_alt=alt,
        image_aspect_ratio=aspect_ratio,
    )

    print('Bluesky post created successfully!')
except Exception as e:
    print(f"Error posting on Bluesky: {e}")
