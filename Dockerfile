FROM python:3.6
MAINTAINER baojw

ADD . /mem_words/
WORKDIR /mem_words
RUN pip install -i 'http://pypi.douban.com/simple' --trusted-host pypi.douban.com -r requirements.txt

EXPOSE 8000
