# /usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import urllib.parse
import urllib.request

import bibtexparser as bp
import nltk
import pytoml
import pyperclip as pc
from summa import keywords, summarizer
from textrank4zh import TextRank4Keyword, TextRank4Sentence

FOR_TEST = True


caiyun_token = "3975l6lr5pcbvidl6jl2"

def get_english_summary(text):
    summary = summarizer.summarize(text)
    # print(summary)
    summary_sentences = [i for i in "".join(summary).split("\n")]
    return summary_sentences

# def get_english_keywords(text):
#     kewords_ = keywords.keywords(text)
#     postags = nltk.pos_tag(kewords_)

#     result = []

#     for (word, tag)


def get_chinese_summary(text):
    tr4s = TextRank4Sentence()
    tr4s.analyze(text=text, lower=True, source='all_filters')

    result = []

    for item in tr4s.get_key_sentences(num=3):
        # print(item.index, item.weight, item.sentence)
        result.append(item.sentence)

    return result


def get_chinese_keywords(text):
    tr4w = TextRank4Keyword()

    tr4w.analyze(text=text, lower=True, window=5)

    keywords_ = []
    for item in tr4w.get_keywords(10, word_min_len=2):
        # print(item.word, item.weight)
        keywords_.append(item.word)

    # print()
    # print( '关键短语：' )
    keyphrases = []
    for phrase in tr4w.get_keyphrases(keywords_num=20, min_occur_num=2):
        keyphrases.append(phrase)

    return keywords_, keyphrases


def caiyun_translate(source):
    """Use CaiYun Translator's  API to translate the abstract

    Args:
        content (str): The content of abstract
    """

    url = "http://api.interpreter.caiyunai.com/v1/translator"
    direction = "auto2zh"

    # WARNING, this token is a test token for new developers, and it should be replaced by your token


    payload = {
        "source": source,
        "trans_type": direction,
        "request_id": "demo",
        "detect": True,
    }

    headers = {
        'content-type': "application/json",
        'x-authorization': "token " + caiyun_token,
    }

    response_data = ""
    req = urllib.request.Request(
        "https://api.interpreter.caiyunai.com/v1/translator")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-authorization", "token " + caiyun_token)

    with urllib.request.urlopen(req, data=json.dumps(payload).encode("utf-8")) as f:
        read_data = f.read()
        response_data = read_data.decode('unicode_escape')

    return json.loads(response_data)['target']


def parse_content(content):
    """Parse the bibtext and translate the abstract

    Args:
        content (str): the bibtex content
    """
    bibs = bp.loads(content)
    entries = bibs.entries

    result = []
    for entry in bibs.entries:
        new_entry = entry
        if "author" in entry.keys():
            new_entry["author"] = entry["author"].split(" and ")
        if "abstractnote" in entry.keys():
            new_entry["abstractnote"] = entry["abstractnote"].replace("\n", "")
            new_entry["abstractnote_cn"] = caiyun_translate(
                entry["abstractnote"])
            english_summary = get_english_summary(new_entry["abstractnote"])
            chinese_summary = get_chinese_summary(new_entry["abstractnote_cn"])
            chinese_keywords, chinese_keyphrase = get_chinese_keywords(
                new_entry["abstractnote_cn"])
            new_entry["english_summary"] = english_summary
            new_entry["chinese_summary"] = chinese_summary
            new_entry["chinese_keywords"] = chinese_keywords
            new_entry["chinese_keyphrase"] = chinese_keyphrase
        # if "doi" in entry.keys():
        #     result.append(new_entry)

    return result


def generate_metadata(entries):
    result = []
    result.append("metadata")
    for entry in entries:
        entry = {k: entry[k] for k in sorted(entry.keys())}
        result.append(f"\t{entry['ID']}")
        result.append(f"\t\t{entry['title']}")
        for key in entry.keys():
            if key != "ID" and key != "title":
                if key == "journal":
                    result.append(f"\t\t{key}: [[{entry[key]}]]")
                elif key == "author":
                    result.append(
                        f"\t\t{key}: {','.join(['[[' + i + ']]' for i in entry[key]])}")
                elif key == "chinese_keywords":
                    result.append(f"\t\t{key}:")
                    for keywords_ in entry["chinese_keywords"]:
                        result.append(f"\t\t\t{keywords_}")
                elif key == "chinese_keyphrase":
                    result.append(f"\t\t{key}:")
                    for keywords_ in entry["chinese_keyphrase"]:
                        result.append(f"\t\t\t{keywords_}")
                elif key == "english_summary":
                    result.append(f"\t\t{key}:")
                    for summary in entry["english_summary"]:
                        result.append(f"\t\t\t{summary}")
                elif key == "chinese_summary":
                    result.append(f"\t\t{key}:")
                    for summary in entry["chinese_summary"]:
                        result.append(f"\t\t\t{summary}")
                elif key == "doi":
                    doi_websites = "https:/doi.org/" +  entry["doi"]
                    result.append(f"\t\t{key}:[{entry['doi']}]({doi_websites})")
                else:
                    result.append(f"\t\t{key}: {entry[key]}")
    return "\n".join(result)


if __name__ == '__main__':
    config = pytoml.load(open("config.toml", "r"))
    caiyun_token = config["caiyun_token"]
    if FOR_TEST:
        print("中文测试")
        clip_content = open("test.bib", 'r').read()
        print(clip_content)
        entries = parse_content(clip_content)
        print(entries)
        result = generate_metadata(entries)
        print(result)
    else:
        clip_content = pc.paste()
        entries = parse_content(clip_content)
        result = generate_metadata(entries)
        pc.copy(result)
