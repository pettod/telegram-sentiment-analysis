import argparse
import json
from highcharts import Highchart
from multiprocessing import cpu_count
from pysentimiento import create_analyzer
from pqdm.threads import pqdm


class Analyzer():
    def __init__(self):
        self.person_1 = {"name": None, "messages": []}
        self.person_2 = {"name": None, "messages": []}
        self.start_date = None
        self.end_date = None
        print("Load sentiment model")
        self.sentiment_analyzer = create_analyzer(task="sentiment", lang="en")
        print("Load emotion model")
        self.emotion_analyzer = create_analyzer(task="emotion", lang="en")

    def __call__(self, file_name):
        self.__parseJson(file_name)
        sentiments_1 = self.__sentimentAnalysis(self.person_1["messages"])
        sentiments_2 = self.__sentimentAnalysis(self.person_2["messages"])
        emotions_1 = self.__emotionAnalysis(self.person_1["messages"])
        emotions_2 = self.__emotionAnalysis(self.person_2["messages"])

        # Absolute charts
        self.__createChart(
            sentiments_1, sentiments_2,
            "Sentiment analysis from Telegram messages",
            "Sentiment",
            "Messages",
            "messages",
            "absolute_sentiment",
        )
        self.__createChart(
            emotions_1, emotions_2,
            "Emotions analysis from Telegram messages",
            "Emotions",
            "Messages",
            "messages",
            "absolute_emotions",
        )

        # Create relative numbers
        def relativeDicts(dict_):
            total = 0
            for d in dict_.keys():
                total += dict_[d]
            for d in dict_.keys():
                dict_[d] = round(dict_[d] / total, 4)
            return dict_
        sentiments_1 = relativeDicts(sentiments_1)
        sentiments_2 = relativeDicts(sentiments_2)
        emotions_1 = relativeDicts(emotions_1)
        emotions_2 = relativeDicts(emotions_2)

        # Relative charts
        self.__createChart(
            sentiments_1, sentiments_2,
            "Sentiment analysis from Telegram messages",
            "Sentiment",
            "Percentage",
            "%",
            "relative_sentiment",
        )
        self.__createChart(
            emotions_1, emotions_2,
            "Emotions analysis from Telegram messages",
            "Emotions",
            "Percentage",
            "%",
            "relative_emotions",
        )

    def __sentimentAnalysis(self, sentences):
        sentiments = {
            "POS": 0,
            "NEU": 0,
            "NEG": 0,
        }
        print("Sentiment analysis")
        def predictSentiment(sentence):
            sentiments[self.sentiment_analyzer.predict(sentence).output] += 1
        pqdm(sentences, predictSentiment, n_jobs=cpu_count())
        #for sentence in pqdm(sentences, n_jobs=cpu_count()):
        #    sentiments[self.sentiment_analyzer.predict(sentence).output] += 1
        sentiments["Positive"] = sentiments.pop("POS")
        sentiments["Neutral"] = sentiments.pop("NEU")
        sentiments["Negative"] = sentiments.pop("NEG")
        return sentiments

    def __emotionAnalysis(self, sentences):
        emotions = {
            "anger": 0,
            "disgust": 0,
            "fear": 0,
            "joy": 0,
            "others": 0,
            "sadness": 0,
            "surprise": 0,
        }
        print("Emotion analysis")
        def predictEmotion(sentence):
            emotions[self.emotion_analyzer.predict(sentence).output] += 1
        pqdm(sentences, predictEmotion, n_jobs=cpu_count())
        #for sentence in pqdm(sentences, n_jobs=cpu_count()):
        #    emotions[self.emotion_analyzer.predict(sentence).output] += 1
        for key in list(emotions.keys()):
            emotions[key.title()] = emotions.pop(key)
        return emotions

    def __createChart(self, data_1, data_2, title, x_axis_label, y_axis_label, unit, save_file_name):
        chart = Highchart()
        options = {
            "chart": {
                "height": "1000px",
            },
            "title": {
                "text": title,
                "style": {
                    "fontSize": "40px",
                },
            },
            "subtitle": {
                "text": "{}+{} messages analyzed between {} and {}".format(
                    sum(data_1.values()),
                    sum(data_2.values()),
                    self.start_date,
                    self.end_date,
                ),
                "style": {
                    "fontSize": "25px",
                },
            },
            "xAxis": {
                "type": "category",
                "reversed": False,
                "title": {
                    "enabled": True,
                    "text": x_axis_label,
                    "style": {
                        "fontSize": "30px",
                    },
                },
                "labels": {
                    "formatter": "function () {\
                        return this.value;\
                    }",
                    "style": {
                        "fontSize": "25px",
                    },
                },
                "showLastLabel": True
            },
            "yAxis": {
                "allowDecimals": False,
                "title": {
                    "text": y_axis_label,
                    "style": {
                        "fontSize": "25px",
                    },
                },
                "labels": {
                    "formatter": "function () {\
                        return this.value;\
                    }",
                    "style": {
                        "fontSize": "25px",
                    },
                },
                "lineWidth": 2
            },
            "legend": {
                "enabled": True,
                "itemStyle": {
                    "fontSize": "17px",
                },
            },
            "tooltip": {
                "headerFormat": "<b>{point.key}</b><br/>",
                "pointFormat": "{series.name}<br/>{point.y} " + unit,
                "style": {
                    "fontSize": "17px",
                },
            },
        }
        chart.set_dict_options(options)
        chart.add_data_set(list(data_1.items()), "bar", self.person_1["name"])
        chart.add_data_set(list(data_2.items()), "bar", self.person_2["name"])
        chart.save_file(save_file_name)

    def __parseJson(self, file_name):
        messages = json.load(open(file_name))["chats"]["list"][0]["messages"]
        for message in messages:

            # Skip pinned messages and phone calls
            if "action" in message.keys():
                continue

            # Extract name and text
            name = message["from"]
            text = message["text"]
            if type(text) == list:
                text = text[0]
            if type(text) == dict:
                text = ""

            # Initialize name
            if self.person_1["name"] is None:
                self.person_1["name"] = name
            elif self.person_2["name"] is None:
                self.person_2["name"] = name

            # Set start and end dates
            if self.start_date is None:
                self.start_date = message["date"][:10]
            self.end_date = message["date"][:10]

            # Add text
            if text != "":
                if name != self.person_1["name"]:
                    self.person_2["messages"].append(text)
                else:
                    self.person_1["messages"].append(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name")
    args = parser.parse_args()

    analyzer = Analyzer()
    analyzer(args.file_name)


main()
