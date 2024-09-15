# Wiki Translate Tagger

## Overview

**Wiki Translate Tagger** is a web tool designed to convert standard wikitext into a format with `<translate>` tags, making it ready for translation. This tool simplifies the process of preparing wikitext content for multilingual support, ensuring that translations are correctly tagged and formatted.

## Features

- **Convert Wikitext**: Input wikitext and convert it into a translatable format with `<translate>` tags.
- **Copy to Clipboard**: Easily copy the converted wikitext to your clipboard for use in translation workflows.
- **Responsive Design**: User-friendly interface that is accessible on both desktop and mobile devices.

## Installation

### Prerequisites

- Python 3.x
- Flask

### Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/indictechcom/translatable-wikitext-converter
   cd wiki-translate-tagger
   ```

2. **Create a Virtual Environment**

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3. **Install Dependencies**

    ```bash
        pip install -r requirements.txt
    ```

4. **Run the Application**
    ```bash
        python app.py
    ```

The application will start on http://127.0.0.1:5000.

## Usage

1. **Open the Application**: Navigate to `http://127.0.0.1:5000` in your web browser.
2. **Enter Wikitext**: Paste your standard wikitext into the input textarea on the left.
3. **Convert to Translatable Wikitext**: Click the "Convert to Translatable Wikitext" button.
4. **Copy Converted Text**: Once the conversion is complete, you can copy the converted text using the "Copy to Clipboard" button.

## Project Structure

- `app.py`: Main application file containing Flask routes and logic.
- `templates/`: Directory containing HTML templates.
  - `index.html`: Main template for the web interface.
- `static/`: Directory for static files (e.g., CSS, JavaScript).
- `requirements.txt`: List of Python dependencies.

## Contributing

We welcome contributions to enhance the Wiki Translate Tagger. If you have suggestions, improvements, or bug fixes, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a pull request on GitHub.

## License

This project is licensed under the [MIT License](LICENSE).


