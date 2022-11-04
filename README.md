
![](/assets/logo_small_centered.png?raw=true "Logo")

Welcome to Lovebot:
An app to automate swiping and texting on Tinder.

## Setup

1. Install python requirements
```bash
pip install -r requirements.txt
```

2. Set the ```LOVEBOT_PATH``` environemt variable. (alternatively, you may create an .env file and place it in the top level of the cloned repository)
```bash
export LOVEBOT_PATH=#path to repository#
```

3. Download .onnx models from [Google Drive](https://drive.google.com/drive/folders/1--AcK0jb6MdYs8x3yeHNzST_9WhN1tHY?usp=share_link)

4. Create Openai API key by registering an account [here](https://openai.com/api/).

5. Create a ```config.ini``` fily by copying the  ```config_template.ini``` and filling in the necessary information.
```
[DEFAULT]
ChromeDataPath=#choose chromedata path#
Name=#your name#
SleepTime=2

[TEXTING]
ManualOvertakeSymbol=..

[SCRAPING]
Count=20
RetryCount=3
ScrapingFolder=#choose path to download scraped imaged#

[MODELS]
Bikini=#enter path to model#
Like=#enter path to model#
OpenAI=#enter openai API key#
```


## Usage

To start the application, simply run
```bash
python app.py
```

## Architecture

![](/assets/lovebot_architecture.drawio.png?raw=true "Architektur")



## License
[MIT](https://choosealicense.com/licenses/mit/)
