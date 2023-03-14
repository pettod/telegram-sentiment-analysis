# Telegram sentiment analysis

## Introduction

Analyze the chat messages one by one and create bar charts to show the results. The following 2 charts are created:

* Sentiment analysis

    * Positive
    * Neutral
    * Negative

* Emotion analysis

    * Anger
    * Disgust
    * Fear
    * Joy
    * Others
    * Sadness
    * Surprise

## How to use

1. Install Telegram Desktop app
1. Export the chat history by going to the person's chat, clicking 3 dots, and "Export chat history". Choose `.json` file format. You have to wait 24 hours and then Telegram lets you to download the chat history. More information here: https://telegram.org/blog/export-and-more
1. Install Python 3.9
1. `pip install -r requirements.txt`
1. The code generates 2 graphs into `.html` files by running the following command

```bash
main.py /path/to/chat_history.json
```
