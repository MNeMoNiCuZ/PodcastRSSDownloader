import feedparser
import os
import requests
import urllib.parse
import time

def safe_folder_name(name):
    """Converts a string to a safe folder name."""
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()

def download_file(url, folder, title, naming_mode):
    """Downloads a file showing progress and checks if the file already exists."""
    url_filename = url.split('/')[-1].split('.mp3')[0]
    safe_title = safe_folder_name(title)
    if naming_mode == "1":
        safe_filename = url_filename
    elif naming_mode == "2":
        safe_filename = safe_title
    elif naming_mode == "3":
        safe_filename = f"{url_filename} - {safe_title}"
    else:  # Default to mode 4
        safe_filename = f"{safe_title} - {url_filename}"
    safe_filename += '.mp3'
    path = os.path.join(folder, safe_filename)
    # Check if the file already exists
    if os.path.exists(path):
        print(f"File {safe_filename} already exists. Skipping download.")
        return
    with requests.get(url, stream=True) as r:
        total_length = int(r.headers.get('content-length', 0))
        with open(path, 'wb') as f:
            if total_length is None or total_length == 0:  # when content-length is unknown
                f.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for chunk in r.iter_content(chunk_size=4096):
                    dl += len(chunk)
                    f.write(chunk)
                    done = int(50 * dl / total_length)
                    print(f"\rDownloading {safe_filename}: [{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f}/{total_length/1024/1024:.2f} MB", end='')
        print()



# Loop to continuously ask for new RSS feed URLs
while True:
    # Asking for the RSS feed URL
    rss_feed_url = input("Enter the URL of the RSS feed (or type 'exit' to quit): ")
    
    # Exit condition
    if rss_feed_url.lower() == 'exit':
        break

    # Parse the RSS feed
    feed = feedparser.parse(rss_feed_url)

    # Extracting and listing the MP3 links, considering different formats
    # Also preparing to display a table of filenames and titles
    print(f"{'Filename':<50} | Title")
    print("-" * 80)
    mp3_files_info = []
    for entry in feed.entries:
        if entry.enclosures:
            enclosure = entry.enclosures[0]
            if enclosure.type == 'audio/mpeg':
                enclosure_url = enclosure['href']
                # Cleaning and validating the URL
                if '?' in enclosure_url:
                    enclosure_url = enclosure_url.split('?')[0]  # Removes query parameters if present
                if enclosure_url.endswith('.mp3'):
                    url_filename = enclosure_url.split('/')[-1].split('.mp3')[0]
                    print(f"{url_filename:<50} | {entry.title}")
                    mp3_files_info.append((enclosure_url, entry.title))

    # Confirm download
    download_confirm = input("Do you want to download all the files? [Y/n]: ") or "Y"

    if download_confirm.lower() == 'y':
        # Choose naming mode
        print("Choose a naming mode for the files:")
        print("1 = Filename")
        print("2 = Title name")
        print("3 = 'Filename - Titlename'")
        print("4 = 'Titlename - Filename'")
        naming_mode = input("Enter your choice (default is 4): ") or "4"

        # Creating the 'Downloaded' folder and a subfolder for the podcast
        base_folder = "Downloaded"
        podcast_name = safe_folder_name(urllib.parse.urlparse(rss_feed_url).path.split('/')[-1])
        podcast_folder = os.path.join(base_folder, podcast_name)
        os.makedirs(podcast_folder, exist_ok=True)

        # Downloading the files based on naming mode
        for url, title in mp3_files_info:
            download_file(url, podcast_folder, title, naming_mode)

        print("\nAll files downloaded successfully.")
    else:
        print("Download canceled.")

    print("\nReady for the next URL.")