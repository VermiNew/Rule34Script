import rule34
import requests
import argparse
import logging
from pathlib import Path
from timeit import default_timer
from colorama import Fore, Style
import tkinter as tk
from tqdm import tqdm
import sys

class Rule34Downloader:
    LOGGING_LEVEL = logging.INFO

    def __init__(self, parameters):
        self.parameters = parameters
        self.setup_logging()

    @staticmethod
    def list_diff(list1, list2):
        return list(set(list1) - set(list2))

    def setup_logging(self):
        self.logger = logging.getLogger("CORE")
        self.logger.setLevel(self.LOGGING_LEVEL)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.LOGGING_LEVEL)

        formatter = logging.Formatter('[%(asctime)s] <%(name)s> <%(levelname)s>: %(message)s')
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def run(self):
        try:
            self.logger.debug("Arguments: {}".format(self.parameters))

            rule34sync = rule34.Sync()

            if len(self.parameters.tags) > 1:
                self.parameters.tags = ' '.join(self.parameters.tags)
            else:
                self.parameters.tags = self.parameters.tags[0]

            self.logger.debug("Querying Rule34 APIs...")
            images_count = rule34sync.totalImages(self.parameters.tags)

            if images_count == 0:
                self.logger.error(f"{Fore.RED}No images found with those tags{Style.RESET_ALL}")
                return

            self.logger.info(f"{Fore.GREEN}{images_count} images found!{Style.RESET_ALL}")

            if self.parameters.limit > 0:
                self.logger.info(f"The download limit is capped to {self.parameters.limit} images")

            self.fetch_and_download_images(rule34sync, images_count)

            if self.parameters.gui:
                self.run_gui()
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred: {str(e)}{Style.RESET_ALL}")

    def fetch_and_download_images(self, rule34sync, images_count):
        self.logger.info(f"{Fore.CYAN}Gathering data from Rule34...{Style.RESET_ALL} "
                         f"(this will take approximately {format(0.002 * images_count, '.3f')} seconds)")

        fetch_start = default_timer()
        try:
            images = rule34sync.getImages(self.parameters.tags, singlePage=False)
        except Exception as e:
            self.logger.error(f"{Fore.RED}There was an error while gathering images.{Style.RESET_ALL}")
            self.logger.error(f"{Fore.RED}There's probably something wrong with this tag; try another one.{Style.RESET_ALL}")
            self.logger.debug(str(e))
            return

        fetch_end = default_timer()

        self.logger.info(f"This took exactly {format((fetch_end - fetch_start) / images_count, '.3f')} seconds")

        if images is None:
            self.logger.error(f"{Fore.RED}Rule34 didn't give any image; this should not happen{Style.RESET_ALL}")
            return

        videos = [x for x in images if "webm" in x.file_url]

        if not self.parameters.no_videos:
            images = self.list_diff(images, videos)

        self.download_images(images)

    def download_images(self, images):
        destination_folder = Path(self.parameters.destination)
        self.logger.debug("Checking destination folder existence...")
        try:
            destination_folder.mkdir(parents=True, exist_ok=True)
            self.logger.debug("Destination folder created or already exists!")
        except Exception as e:
            self.logger.error("Error creating the destination folder.")
            self.logger.error(str(e))
            return

        downloaded_images = 0
        for image in images:
            if 0 < self.parameters.limit <= downloaded_images:
                self.logger.warning(f"{Fore.YELLOW}Downloaded images limit exceeded. Stopping...{Style.RESET_ALL}")
                return

            self.download_image(image, destination_folder)
            downloaded_images += 1
            print(f"Downloaded images: {downloaded_images}")

    def download_image(self, image, destination_folder):
        image_name = image.file_url.split("/")[-1]
        image_extension = image.file_url.rsplit('.', 1)[-1]

        output_name = Path(destination_folder, '.'.join([image.md5, image_extension]))
        self.logger.debug(f"Output file: {output_name}")
        self.logger.info(f"Downloading {image_name}...")

        response = requests.get(image.file_url, stream=True)
        self.logger.debug(f"API response is {response.status_code}")

        if response.status_code != 200:
            self.logger.error(f"Error while downloading image! ({response.status_code})")
            return

        total_size_in_bytes = int(response.headers.get('content-length', 0))

        with open(output_name, 'wb') as output_file:
            with tqdm(total=total_size_in_bytes, unit='B', unit_scale=True, desc=f"Downloading {image_name}") as pbar:
                for chunk in response.iter_content(1024):
                    output_file.write(chunk)
                    pbar.update(len(chunk))

        self.logger.info(f"{image_name} downloaded!")

    def run_gui(self):
        def start_download():
            tags = tags_entry.get().split()
            destination = destination_entry.get()
            limit = int(limit_entry.get())
            no_videos = no_videos_var.get()

            params = argparse.Namespace(tags=tags, destination=destination, limit=limit, no_videos=no_videos, gui=True)
            Rule34Downloader(params).run()

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

def print_help():
    help_text = f"""{Fore.CYAN}Rule34 Downloader Help{Style.RESET_ALL}

{Fore.YELLOW}Usage:{Style.RESET_ALL}
    script.py [options]

{Fore.YELLOW}Options:{Style.RESET_ALL}
    {Fore.GREEN}-h, --help{Style.RESET_ALL}                      Show this help message and exit. {Fore.CYAN}(Optional){Style.RESET_ALL}
    {Fore.GREEN}-t, --tags TAGS{Style.RESET_ALL}                 Required. Specify search tags for images on Rule34. Enclose multiple tags in quotes. {Fore.RED}(Required){Style.RESET_ALL}
    {Fore.GREEN}-d, --destination DESTINATION{Style.RESET_ALL}   Specify the destination directory for downloads. Default is 'data'. {Fore.CYAN}(Optional){Style.RESET_ALL}
    {Fore.GREEN}-l, --limit LIMIT{Style.RESET_ALL}               Set a limit for the number of downloads. 0 for unlimited. Default is 0. {Fore.CYAN}(Optional){Style.RESET_ALL}
    {Fore.GREEN}-nv, --no-videos{Style.RESET_ALL}                Exclude videos, download only images. {Fore.CYAN}(Optional){Style.RESET_ALL}
    {Fore.GREEN}-g, --gui{Style.RESET_ALL}                       Launch in GUI mode for interactive use. {Fore.CYAN}(Optional){Style.RESET_ALL}

{Fore.YELLOW}Examples:{Style.RESET_ALL}
    {Fore.LIGHTCYAN_EX}script.py {Fore.CYAN}-t{Style.RESET_ALL} {Fore.LIGHTMAGENTA_EX}"tag1 tag2"{Style.RESET_ALL} {Fore.CYAN}-d{Style.RESET_ALL} {Fore.LIGHTMAGENTA_EX}C:\\Path\\...{Style.RESET_ALL} {Fore.CYAN}-l{Style.RESET_ALL} {Fore.LIGHTMAGENTA_EX}100{Style.RESET_ALL}
        Downloads up to 100 files with 'tag1' and 'tag2' to the specified directory.

    {Fore.LIGHTCYAN_EX}script.py {Fore.CYAN}--tags{Style.RESET_ALL} {Fore.LIGHTMAGENTA_EX}"anime"{Style.RESET_ALL} {Fore.CYAN}--no-videos{Style.RESET_ALL}
        Downloads images with the tag 'anime', excluding videos, to the default 'data' directory.

    {Fore.LIGHTCYAN_EX}script.py {Fore.CYAN}-g{Style.RESET_ALL}
        Launches the downloader in GUI mode.

{Fore.RED}Important Notes:{Style.RESET_ALL}
    - {Fore.YELLOW}Ensure you're entering existing tags{Style.RESET_ALL} to avoid empty search results.
    - Avoid using {Fore.CYAN}disallowed characters in file names{Style.RESET_ALL} such as {Fore.CYAN}/:*?"<>|{Style.RESET_ALL} when specifying the destination path.
    - {Fore.GREEN}Verify that there is enough disk space{Style.RESET_ALL} before initiating large downloads. The size of the files, especially high-quality images and videos, can be substantial.
    - Be mindful of {Fore.LIGHTRED_EX}network bandwidth consumption{Style.RESET_ALL} when downloading many files or videos.\n      {Fore.LIGHTYELLOW_EX}Extensive downloads can significantly affect network performance and might lead to extra charges on metered connections.{Style.RESET_ALL}"""
    print(help_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rule34 posts downloader", add_help=False)
    parser.add_argument('--tags', '-t', type=str, nargs='+',
                        help='the actual tags to search')
    parser.add_argument('--destination', '-d', type=str, default='data',
                        help='the destination folder of the downloaded material (default: data)')
    parser.add_argument('--limit', '-l', type=int, default=0,
                        help='the maximum amount of material to download (default: 0 [no limit])')
    parser.add_argument('--no-videos', '-nv', action='store_true',
                        help="don't download videos")
    parser.add_argument('--gui', '-g', action='store_true',
                        help="enable GUI mode")
    parser.add_argument('--help', '-h', action='store_true', help='Shows the help information')

    args = parser.parse_args()

    if '--help' in sys.argv or '-h' in sys.argv or '-t' not in sys.argv and '--tags' not in sys.argv:
        print_help()
        sys.exit()

    logo = r'''
    ____  _  _  __    ____  ____   ___    ____   __   _  _  __ _  __     __    __   ____  ____  ____ 
    (  _ \/ )( \(  )  (  __)( __ \ / _ \  (    \ /  \ / )( \(  ( \(  )   /  \  / _\ (    \(  __)(  _ \
     )   /) \/ (/ (_/\ ) _)  (__ ((__  (   ) D ((  O )\ /\ //    // (_/\(  O )/    \ ) D ( ) _)  )   /
    (__\_)\____/\____/(____)(____/  (__/  (____/ \__/ (_/\_)\_)__)\____/ \__/ \_/\_/(____/(____)(__\_)
    '''
    print(logo)
    print('=' * len(max(logo.split('\n'), key=len)) + '=' * 4)
    print()

    downloader = Rule34Downloader(args)
    downloader.run()
