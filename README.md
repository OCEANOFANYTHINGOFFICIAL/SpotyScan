# SpotyScan

![GitHub license](https://img.shields.io/github/license/OCEANOFANYTHINGOFFICIAL/SpotyScan)
![GitHub stars](https://img.shields.io/github/stars/OCEANOFANYTHINGOFFICIAL/SpotyScan)
![GitHub forks](https://img.shields.io/github/forks/OCEANOFANYTHINGOFFICIAL/SpotyScan)
![GitHub issues](https://img.shields.io/github/issues/OCEANOFANYTHINGOFFICIAL/SpotyScan)

SpotyScan is a Python-based application designed to download and process Spotify track cover images and their corresponding scannable codes with advanced customization features.

## Features

### 1. Single Track Cover Image Download
- Download the cover image for a single Spotify track.

### 2. Playlist Cover Image Download
- Download cover images for all tracks in a Spotify playlist.

### 3. Bulk Song Link Cover Image Download
- Download cover images for multiple tracks specified in a text file.

### 4. Cover Images with Spotify Codes
- Generate scannable Spotify codes for single or multiple tracks.

### 5. Image Combination Functionality
- Combine track cover images with their corresponding Spotify codes into a single image.

### 6. Color-Adaptive Spotify Codes
- Extract the most used color from cover images and determine the optimal barcode color (black/white) based on contrast.
- Generate customized Spotify codes using the best bar and background colors.

### 7. Folder Merging Option
- Merge song covers and Spotify codes from separate folders into a single output folder.

### 8. Most Used Color Picker for Spotify Codes
- Automatically picks the most used color from cover images to customize Spotify codes.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/OCEANOFANYTHINGOFFICIAL/SpotyScan.git
   ```
2. Navigate to the project directory:
   ```bash
   cd SpotyScan
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```
2. Follow the on-screen prompts to choose the desired operation.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](https://github.com/OCEANOFANYTHINGOFFICIAL/SpotyScan/blob/main/LICENSE) file for details.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## Issues

If you encounter any issues, please report them [here](https://github.com/OCEANOFANYTHINGOFFICIAL/SpotyScan/issues).

## Acknowledgments

- Thanks to the developers of the libraries used in this project, including `requests`, `Pillow`, and `colorama`.
