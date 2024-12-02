import requests
import re
import os
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from collections import Counter
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Helper function to print colored messages
def print_status(message, status="INFO"):
    status_colors = {
        "SUCCESS": Fore.GREEN,
        "INFO": Fore.CYAN,
        "ERROR": Fore.RED,
        "WARNING": Fore.YELLOW,
        "STATUS": Fore.MAGENTA
    }
    color = status_colors.get(status, Fore.WHITE)
    print(f"{color}[{status}] {message}")

# Helper function to print colored messages
def print_colored(message, color=Fore.WHITE):
    print(f"{color}{message}")

# Spotify API credentials
CLIENT_ID = ""
CLIENT_SECRET = ""

# Function to get Spotify API access token
def get_access_token():
    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": f"Basic {CLIENT_ID}:{CLIENT_SECRET}"}
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print_status(f"Error: Unable to fetch access token. {response.json()}", "ERROR")
        return None

# Function to fetch album cover URL
def fetch_cover_image(spotify_url):
    # Extract the Spotify ID from the URL
    spotify_id = spotify_url.split("/")[-1].split("?")[0]

    # Get the access token
    access_token = get_access_token()
    if not access_token:
        return None

    # Make a request to the Spotify API
    url = f"https://api.spotify.com/v1/tracks/{spotify_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        track_data = response.json()
        # Fetch the largest available album cover image
        album_images = track_data["album"]["images"]
        if album_images:
            album_images.sort(key=lambda x: x['height'], reverse=True)
            album_cover_url = album_images[0]["url"]
            
            track_name = track_data["name"]
            
            # Replace spaces and sanitize the track name to create a valid filename
            sanitized_track_name = re.sub(r'[\s\\/*?"<>|]', "-", track_name)
            
            # Further sanitize track name to ensure no illegal characters
            sanitized_track_name = re.sub(r'[<>:"/\\|?*]', "-", sanitized_track_name)
            
            print_status(f"Fetching cover image from URL: {album_cover_url}", "INFO")
            
            return album_cover_url, sanitized_track_name
        else:
            print_status("No images found for the track.", "WARNING")
            return None, None
    else:
        print_status(f"Error: Unable to fetch track data. {response.json()}", "ERROR")
        return None, None

# Function to download image
def download_image(session, album_cover_url, sanitized_playlist_name, sanitized_track_name):
    # Download and save the album cover image
    image_response = session.get(album_cover_url)
    if image_response.status_code == 200:
        with open(os.path.join(sanitized_playlist_name, f"{sanitized_track_name}.jpg"), "wb") as file:
            file.write(image_response.content)
        print_status(f"Image saved as {sanitized_track_name}.jpg in {sanitized_playlist_name} folder", "SUCCESS")
    else:
        print_status(f"Failed to download the cover image for {sanitized_track_name}.", "ERROR")

# Function to get the most used color in an image
def get_most_used_color(image_path):
    if not os.path.exists(image_path):
        print_status(f"File not found: {image_path}", "ERROR")
        return None

    with Image.open(image_path) as img:
        img = img.convert('RGB')
        pixels = list(img.getdata())
        most_common_color = Counter(pixels).most_common(1)[0][0]
        return most_common_color

# Function to determine the best bar color
def determine_best_bar_color(most_used_color):
    # Calculate luminance of the most used color
    luminance = (0.299 * most_used_color[0] + 0.587 * most_used_color[1] + 0.114 * most_used_color[2])
    return "white" if luminance < 128 else "black"

# Function to download Spotify code image with color customization
def download_custom_spotify_code_image(session, spotify_uri, output_path, background_color, bar_color):
    url = f"https://scannables.scdn.co/uri/plain/jpeg/{background_color}/{bar_color}/640/{spotify_uri}"
    response = session.get(url)
    if response.status_code == 200:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as file:
            file.write(response.content)
        print_status(f"Spotify code saved as {output_path}", "SUCCESS")
    else:
        print_status(f"Failed to download Spotify code for {spotify_uri}.", "ERROR")

# Function to combine cover and Spotify code images
def combine_images(cover_image_path, code_image_path, output_path):
    # Ensure the output directory exists
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Combine images
    cover_image = Image.open(cover_image_path)
    code_image = Image.open(code_image_path)

    # Create a new image with space for both cover and code
    total_height = cover_image.height + code_image.height
    combined_image = Image.new('RGB', (cover_image.width, total_height))

    # Paste the images
    combined_image.paste(cover_image, (0, 0))
    combined_image.paste(code_image, (0, cover_image.height))

    combined_image.save(output_path)
    print_status(f"Combined image saved as {output_path}", "SUCCESS")

# Function to fetch playlist details and download cover images for all tracks
def download_playlist_images(playlist_url):
    # Extract the Spotify ID from the URL
    playlist_id = playlist_url.split("/")[-1].split("?")[0]

    # Get the access token
    access_token = get_access_token()
    if not access_token:
        return None

    # Make a request to the Spotify API to get playlist details
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        playlist_data = response.json()
        playlist_name = playlist_data["name"]

        # Sanitize playlist name for directory
        sanitized_playlist_name = re.sub(r'[\s\\/*?"<>|]', "-", playlist_name)
        os.makedirs(sanitized_playlist_name, exist_ok=True)

        with requests.Session() as session:
            with ThreadPoolExecutor(max_workers=5) as executor:
                # Iterate over tracks in the playlist
                for item in playlist_data["tracks"]["items"]:
                    track = item["track"]
                    if not track or not track.get("album") or not track.get("name"):
                        print_status("Skipping unavailable track.", "WARNING")
                        continue

                    track_name = track["name"]
                    album_images = track["album"]["images"]
                    if album_images:
                        album_images.sort(key=lambda x: x['height'], reverse=True)
                        album_cover_url = album_images[0]["url"]

                        # Sanitize track name for filename
                        sanitized_track_name = re.sub(r'[\s\\/*?"<>|]', "-", track_name)
                        sanitized_track_name = re.sub(r'[<>:"/\\|?*]', "-", sanitized_track_name)

                        # Submit download task to the executor
                        executor.submit(download_image, session, album_cover_url, sanitized_playlist_name, sanitized_track_name)
                    else:
                        print_status(f"No images found for {track_name}.", "WARNING")
        return playlist_data
    else:
        print_status(f"Error: Unable to fetch playlist data. {response.json()}", "ERROR")
        return None

def fetch_track_name(spotify_id):
    access_token = get_access_token()
    if not access_token:
        return "Unknown Track"

    url = f"https://api.spotify.com/v1/tracks/{spotify_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        track_data = response.json()
        return track_data.get("name", "Unknown Track")
    else:
        return "Unknown Track"

def process_single_song(spotify_url):
    album_cover_url, sanitized_track_name = fetch_cover_image(spotify_url)

    if album_cover_url:
        print_status(f"Cover Image URL: {album_cover_url}", "INFO")
        with requests.Session() as session:
            image_response = session.get(album_cover_url)
            if image_response.status_code == 200:
                with open(f"{sanitized_track_name}.jpg", "wb") as file:
                    file.write(image_response.content)
                print_status(f"Cover image saved as {sanitized_track_name}.jpg", "SUCCESS")
            else:
                print_status("Failed to download the cover image.", "ERROR")
    else:
        print_status("Failed to fetch the cover image URL.", "ERROR")

def process_playlist(playlist_url):
    download_playlist_images(playlist_url)

def process_song_links_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    output_folder_name = os.path.splitext(os.path.basename(file_path))[0]
    os.makedirs(output_folder_name, exist_ok=True)

    for line in lines:
        spotify_url = line.strip()
        if spotify_url:
            album_cover_url, sanitized_track_name = fetch_cover_image(spotify_url)
            if album_cover_url:
                with requests.Session() as session:
                    image_response = session.get(album_cover_url)
                    if image_response.status_code == 200:
                        with open(os.path.join(output_folder_name, f"{sanitized_track_name}.jpg"), "wb") as file:
                            file.write(image_response.content)
                        print_status(f"Cover image saved as {sanitized_track_name}.jpg in {output_folder_name}", "SUCCESS")
                    else:
                        print_status(f"Failed to download the cover image for {sanitized_track_name}.", "ERROR")
            else:
                print_status(f"Failed to fetch the cover image URL for {spotify_url}.", "ERROR")

def process_single_song_with_code(spotify_url):
    album_cover_url, sanitized_track_name = fetch_cover_image(spotify_url)

    if album_cover_url:
        print_status(f"Cover Image URL: {album_cover_url}", "INFO")
        with requests.Session() as session:
            image_response = session.get(album_cover_url)
            if image_response.status_code == 200:
                with open(f"{sanitized_track_name}.jpg", "wb") as file:
                    file.write(image_response.content)
                print_status(f"Cover image saved as {sanitized_track_name}.jpg", "SUCCESS")
            else:
                print_status("Failed to download the cover image.", "ERROR")
    else:
        print_status("Failed to fetch the cover image URL.", "ERROR")

    # Extract the Spotify ID from the URL
    spotify_id = spotify_url.split("/")[-1].split("?")[0]

    # Get most used color
    most_used_color = get_most_used_color(f"{sanitized_track_name}.jpg")
    if most_used_color is None:
        print_status(f"Skipping {sanitized_track_name} due to missing cover image.", "WARNING")
        return

    background_color = '{:02x}{:02x}{:02x}'.format(*most_used_color)

    # Determine best bar color
    bar_color = determine_best_bar_color(most_used_color)

    # Download Spotify code image with custom colors
    spotify_uri = f"spotify:track:{spotify_id}"
    code_output_path = os.path.join("Spotify_Codes", f"{spotify_id}_code.png")
    download_custom_spotify_code_image(session, spotify_uri, code_output_path, background_color, bar_color)

    # Combine images
    cover_image_path = f"{sanitized_track_name}.jpg"
    combined_output_path = os.path.join("Combined_Images", f"{sanitized_track_name}.jpg")
    combine_images(cover_image_path, code_output_path, combined_output_path)

    # Clean up individual images after combining
    os.remove(cover_image_path)
    os.remove(code_output_path)

def process_playlist_with_code(playlist_url):
    playlist_data = download_playlist_images(playlist_url)

    # Ensure playlist_data is returned and valid
    if not playlist_data:
        print_status("Failed to fetch playlist data.", "ERROR")
    else:
        # Download Spotify codes and combine images
        with requests.Session() as session:
            sanitized_playlist_name = re.sub(r'[\s\\/*?"<>|]', "-", playlist_data["name"])
            for item in playlist_data["tracks"]["items"]:
                track = item["track"]
                if not track or not track.get("album") or not track.get("name"):
                    print_status("Skipping unavailable track.", "WARNING")
                    continue

                track_name = track["name"]
                spotify_uri = track["uri"]

                # Sanitize track name for filename
                sanitized_track_name = re.sub(r'[\s\\/*?"<>|]', "-", track_name)
                sanitized_track_name = re.sub(r'[<>:"/\\|?*]', "-", sanitized_track_name)

                # Get most used color
                most_used_color = get_most_used_color(os.path.join(sanitized_playlist_name, f"{sanitized_track_name}.jpg"))
                if most_used_color is None:
                    print_status(f"Skipping {sanitized_track_name} due to missing cover image.", "WARNING")
                    continue

                background_color = '{:02x}{:02x}{:02x}'.format(*most_used_color)

                # Determine best bar color
                bar_color = determine_best_bar_color(most_used_color)

                # Download Spotify code image with custom colors
                code_output_path = os.path.join("Spotify_Codes", f"{sanitized_track_name}_code.png")
                download_custom_spotify_code_image(session, spotify_uri, code_output_path, background_color, bar_color)

                # Combine images
                cover_image_path = os.path.join(sanitized_playlist_name, f"{sanitized_track_name}.jpg")
                combined_output_path = os.path.join("Combined_Images", f"{sanitized_track_name}.jpg")
                combine_images(cover_image_path, code_output_path, combined_output_path)

                # Clean up individual images after combining
                os.remove(cover_image_path)
                os.remove(code_output_path)

            # After processing, delete the Spotify_Codes and normal images folder
            import shutil
            shutil.rmtree("Spotify_Codes", ignore_errors=True)
            shutil.rmtree(sanitized_playlist_name, ignore_errors=True)

            # Rename the Combined_Images folder to the playlist name
            os.rename("Combined_Images", sanitized_playlist_name)
            print_status(f"Renamed Combined_Images to {sanitized_playlist_name}", "SUCCESS")

def process_song_links_with_code_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    output_folder_name = os.path.splitext(os.path.basename(file_path))[0]
    os.makedirs(output_folder_name, exist_ok=True)

    for line in lines:
        spotify_url = line.strip()
        if spotify_url:
            album_cover_url, sanitized_track_name = fetch_cover_image(spotify_url)
            if album_cover_url:
                spotify_id = spotify_url.split("/")[-1].split("?")[0]
                spotify_uri = f"spotify:track:{spotify_id}"
                with requests.Session() as session:
                    image_response = session.get(album_cover_url)
                    if image_response.status_code == 200:
                        with open(os.path.join(output_folder_name, f"{sanitized_track_name}.jpg"), "wb") as file:
                            file.write(image_response.content)
                        print_status(f"Cover image saved as {sanitized_track_name}.jpg in {output_folder_name}", "SUCCESS")
                    else:
                        print_status(f"Failed to download the cover image for {sanitized_track_name}.", "ERROR")

                # Get most used color
                most_used_color = get_most_used_color(os.path.join(output_folder_name, f"{sanitized_track_name}.jpg"))
                if most_used_color is None:
                    print_status(f"Skipping {sanitized_track_name} due to missing cover image.", "WARNING")
                    continue

                background_color = '{:02x}{:02x}{:02x}'.format(*most_used_color)

                # Determine best bar color
                bar_color = determine_best_bar_color(most_used_color)

                # Download Spotify code image with custom colors
                code_output_path = os.path.join(output_folder_name, f"{sanitized_track_name}_code.png")
                download_custom_spotify_code_image(session, spotify_uri, code_output_path, background_color, bar_color)

                # Combine images
                combined_output_path = os.path.join(output_folder_name, f"{sanitized_track_name}.jpg")
                combine_images(os.path.join(output_folder_name, f"{sanitized_track_name}.jpg"), code_output_path, combined_output_path)

                # Clean up individual images after combining
                os.remove(os.path.join(output_folder_name, f"{sanitized_track_name}_code.png"))

def merge_folders(cover_folder, code_folder, output_folder):
    import os
    from PIL import Image

    os.makedirs(output_folder, exist_ok=True)

    cover_files = sorted(os.listdir(cover_folder))
    code_files = sorted(os.listdir(code_folder))

    for cover_file, code_file in zip(cover_files, code_files):
        cover_path = os.path.join(cover_folder, cover_file)
        code_path = os.path.join(code_folder, code_file)

        if not os.path.exists(cover_path):
            print_status(f"File not found: {cover_path}", "ERROR")
            continue

        if not os.path.exists(code_path):
            print_status(f"File not found: {code_path}", "ERROR")
            continue

        with Image.open(cover_path) as cover_img, Image.open(code_path) as code_img:
            # Create a new image with the height of both images combined
            combined_img = Image.new('RGB', (cover_img.width, cover_img.height + code_img.height))
            combined_img.paste(cover_img, (0, 0))
            combined_img.paste(code_img, (0, cover_img.height))

            # Save the combined image with the same name as the cover
            combined_img.save(os.path.join(output_folder, cover_file))

            print_status(f"Merged {cover_file} with {code_file} into {output_folder}", "SUCCESS")

# Main program
if __name__ == "__main__":
    print_colored("Choose an option:", Fore.CYAN)
    print_colored("1. Normal Cover Image Download", Fore.CYAN)
    print_colored("2. Download Cover Images with Spotify Codes", Fore.CYAN)
    print_colored("3. Merge song covers and Spotify codes from separate folders", Fore.CYAN)
    choice = input("Enter 1, 2, or 3: ")

    if choice == "1":
        print_colored("Choose an option:", Fore.CYAN)
        print_colored("1. Download cover image for a single song", Fore.CYAN)
        print_colored("2. Download cover images for a playlist", Fore.CYAN)
        print_colored("3. Download cover images for a list of song links in a text file", Fore.CYAN)
        sub_choice = input("Enter 1, 2, or 3: ")

        if sub_choice == "1":
            spotify_url = input("Enter the Spotify URL for the song: ")
            process_single_song(spotify_url)
        elif sub_choice == "2":
            playlist_url = input("Enter the Spotify URL for the playlist: ")
            process_playlist(playlist_url)
        elif sub_choice == "3":
            file_path = input("Enter the path to the text file containing song links: ")
            process_song_links_from_file(file_path)
        else:
            print_status("Invalid choice. Please enter 1, 2, or 3.", "ERROR")

    elif choice == "2":
        print_colored("Choose an option:", Fore.CYAN)
        print_colored("1. Download cover image and Spotify code for a single song", Fore.CYAN)
        print_colored("2. Download cover images and Spotify codes for a playlist", Fore.CYAN)
        print_colored("3. Download cover images and Spotify codes for a list of song links in a text file", Fore.CYAN)
        sub_choice = input("Enter 1, 2, or 3: ")

        if sub_choice == "1":
            spotify_url = input("Enter the Spotify URL for the song: ")
            process_single_song_with_code(spotify_url)
        elif sub_choice == "2":
            playlist_url = input("Enter the Spotify URL for the playlist: ")
            process_playlist_with_code(playlist_url)
        elif sub_choice == "3":
            file_path = input("Enter the path to the text file containing song links: ")
            process_song_links_with_code_from_file(file_path)
        else:
            print_status("Invalid choice. Please enter 1, 2, or 3.", "ERROR")

    elif choice == "3":
        cover_folder = input("Enter the path to the folder containing song covers: ")
        code_folder = input("Enter the path to the folder containing Spotify codes: ")
        output_folder = input("Enter the name for the output folder (default: merged): ") or "merged"
        merge_folders(cover_folder, code_folder, output_folder)
    else:
        print_status("Invalid choice. Please enter 1, 2, or 3.", "ERROR")

    # After processing, delete the Spotify_Codes folder
    import shutil
    shutil.rmtree("Spotify_Codes", ignore_errors=True)
