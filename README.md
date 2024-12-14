# ai-srt-translator
A Python script to translate `.srt` subtitle files using OpenAI's GPT-4o model.

## Usage
```bash
python3 translate_srt.py path/to/file.srt destination_language
```
The translated `.srt` file will be saved in the same original file's directory.

## Requirements
- Python 3.8+
- `AIOHTTP`
- OpenAI API key in a `config.ini` file (in a folder with the script file):
```ini
[openai]
api_key = your_api_key_here
```
