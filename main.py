import rule34
import requests
import argparse
import logging
from pathlib import Path
from timeit import default_timer
from colorama import Fore, Style
import tkinter as tk
from tqdm import tqdm

LOGGING_LEVEL = logging.INFO


def list_diff(list1, list2):
    return list(set(list1) - set(list2))


def main(parameters):
    try:
        logger = logging.getLogger("CORE")
        logger.setLevel(LOGGING_LEVEL)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOGGING_LEVEL)

        formatter = logging.Formatter('[%(asctime)s] <%(name)s> <%(levelname)s>: %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        logger.debug("Arguments: {}".format(parameters))

        rule34sync = rule34.Sync()

        if len(parameters.tags) > 1:
            parameters.tags = ' '.join(parameters.tags)
        else:
            parameters.tags = parameters.tags[0]

        logger.debug("Querying Rule34 APIs...")
        images_count = rule34sync.totalImages(parameters.tags)

        if images_count == 0:
            logger.error(f"{Fore.RED}No images found with those tags{Style.RESET_ALL}")
            return

        logger.info(f"{Fore.GREEN}{images_count} images found!{Style.RESET_ALL}")

        if parameters.limit > 0:
            logging.info(f"The download limit is capped to {parameters.limit} images")

        logger.info(f"{Fore.CYAN}Gathering data from Rule34...{Style.RESET_ALL} "
                    f"(this will take approximately {format(0.002 * images_count, '.3f')} seconds)")

        fetch_start = default_timer()
        try:
            images = rule34sync.getImages(parameters.tags, singlePage=False)
        except Exception as e:
            logger.error(f"{Fore.RED}There was an error while gathering images.{Style.RESET_ALL}")
            logger.error(f"{Fore.RED}There's probably something wrong with this tag; try another one.{Style.RESET_ALL}")
            logger.debug(str(e))
            return

        fetch_end = default_timer()

        logger.info(f"This took exactly {format((fetch_end - fetch_start) / images_count, '.3f')} seconds")

        if images is None:
            logger.error(f"{Fore.RED}Rule34 didn't give any image; this should not happen{Style.RESET_ALL}")
            return

        videos = [x for x in images if "webm" in x.file_url]

        if not parameters.no_videos:
            images = list_diff(images, videos)

        destination_folder = Path(parameters.destination)

        logger.debug("Checking destination folder existence...")
        try:
            destination_folder.mkdir(parents=True, exist_ok=True)
            logger.debug("Destination folder created or already exists!")
        except Exception as e:
            logger.error("Error creating the destination folder.")
            logger.error(str(e))
            return

        downloaded_images = 0
        for image in images:
            if 0 < parameters.limit <= downloaded_images:
                logger.warning(f"{Fore.YELLOW}Downloaded images limit exceeded. Stopping...{Style.RESET_ALL}")
                return

            image_name = image.file_url.split("/")[-1]
            image_extension = image.file_url.rsplit('.', 1)[-1]

            output_name = Path(destination_folder, '.'.join([image.md5, image_extension]))
            logger.debug(f"Output file: {output_name}")
            logger.info(f"Downloading {image_name}...")

            response = requests.get(image.file_url, stream=True)
            logger.debug(f"API response is {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Error while downloading image! ({response.status_code})")
                continue

            total_size_in_bytes = int(response.headers.get('content-length', 0))

            with open(output_name, 'wb') as output_file:
                with tqdm(total=total_size_in_bytes, unit='B', unit_scale=True, desc=f"Downloading {image_name}") as pbar:
                    for chunk in response.iter_content(1024):
                        output_file.write(chunk)
                        pbar.update(len(chunk))

            logger.info(f"{image_name} downloaded!")
            downloaded_images += 1
            print(f"Downloaded images: {downloaded_images}")

        if parameters.gui:
            run_gui()

    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred: {str(e)}{Style.RESET_ALL}")


def run_gui():
    def start_download():
        tags = tags_entry.get().split()
        destination = destination_entry.get()
        limit = int(limit_entry.get())
        no_videos = no_videos_var.get()

        params = argparse.Namespace(tags=tags, destination=destination, limit=limit, no_videos=no_videos, gui=True)
        main(params)

    root = tk.Tk()
    root.title("Rule34 Downloader GUI")

    tags_label = tk.Label(root, text="Tags:")
    tags_entry = tk.Entry(root, width=50)

    destination_label = tk.Label(root, text="Destination:")
    destination_entry = tk.Entry(root, width=50)

    limit_label = tk.Label(root, text="Limit:")
    limit_entry = tk.Entry(root, width=5)

    no_videos_var = tk.BooleanVar()
    no_videos_checkbox = tk.Checkbutton(root, text="No Videos", variable=no_videos_var)

    start_button = tk.Button(root, text="Start Download", command=start_download)

    tags_label.pack()
    tags_entry.pack()

    destination_label.pack()
    destination_entry.pack()

    limit_label.pack()
    limit_entry.pack()

    no_videos_checkbox.pack()

    start_button.pack()

    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rule34 posts downloader")
    parser.add_argument('--tags', '-t', type=str, nargs='+', required=True,
                        help='the actual tags to search')
    parser.add_argument('--destination', '-d', type=str, default='data',
                        help='the destination folder of the downloaded material (default: data)')
    parser.add_argument('--limit', '-l', type=int, default=0,
                        help='the maximum amount of material to download (default: unlimited)')
    parser.add_argument('--no-videos', '-nv', action='store_true')
    parser.add_argument('--gui', action='store_true', help='display a graphical user interface')

    args = parser.parse_args()

    logo = fr'''
    ____  _  _  __    ____  ____   ___    ____   __   _  _  __ _  __     __    __   ____  ____  ____ 
    (  _ \/ )( \(  )  (  __)( __ \ / _ \  (    \ /  \ / )( \(  ( \(  )   /  \  / _\ (    \(  __)(  _ \
     )   /) \/ (/ (_/\ ) _)  (__ ((__  (   ) D ((  O )\ /\ //    // (_/\(  O )/    \ ) D ( ) _)  )   /
    (__\_)\____/\____/(____)(____/  (__/  (____/ \__/ (_/\_)\_)__)\____/ \__/ \_/\_/(____/(____)(__\_)
    '''
    print(logo)
    print('=' * len(max(logo.split('\n'), key=len)) + '=' * 4)
    print()

    if args.gui:
        run_gui()
    else:
        main(args)
