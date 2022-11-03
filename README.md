
![](/assets/logo_small_centered.png?raw=true "Logo")

Welcome to Lovebot:
An App to automate swiping and texting on Tinder.

## Setup

1. Install python requirements
```bash
pip install -r requirements.txt
```

2. Set the ```LOVEBOT_PATH``` environemt variable. (alternatively, you may create an .env file and place it in the top level of the cloned repository)
```bash
export LOVEBOT_PATH=#path to repository#
```


3. Download classification models from 

4. Create Openai API key by registering an Account [here](https://openai.com/api/).

5. Add info to the  ```config.ini ``` file
```
[MODELS]
Bikini=#enter path to model#
Like=#enter path to model#
OpenAI=#enter openai API key
```


## Usage

To start the application, simply run
```bash
python app.py
```


## License
[MIT](https://choosealicense.com/licenses/mit/)
