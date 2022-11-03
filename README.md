# lovebot

![](/assets/data.png?raw=true "Dataset")


Foobar is a Python library for dealing with word pluralization.

## Installation

Clone repository

Install requirements
```bash
pip install -r requirements.txt
```

create .env file or add config path as ENV variable
```
LOVEBOT_PATH=#add path to repository#
```

Download classification models

Create openai API key

specify config file


## Usage

```python
import foobar

# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)

