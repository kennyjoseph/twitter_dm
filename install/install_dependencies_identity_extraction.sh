#!/bin/bash
python -m nltk.downloader all

# Download the GloVe data
wget https://dl.dropboxusercontent.com/u/53207718/glove.twitter.27B.50d.gensim_ready.txt.gz

# Download the ARK Brown clusters
wget http://www.ark.cs.cmu.edu/TweetNLP/clusters/50mpaths2

## I COULD NOT GET THIS VERSION TO WORK SO LINKING TO MY OWN
#git clone https://github.com/ikekonglp/TweeboParser.git
wget https://dl.dropboxusercontent.com/u/53207718/TweeboParser.zip
unzip TweeboParser.zip
cd TweeboParser
./install.sh
cd ../

wget https://dl.dropboxusercontent.com/u/53207718/rule_based_model.jar