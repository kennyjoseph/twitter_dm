#!/bin/sh
# Copyright (c) 2013-2014 Lingpeng Kong
# All Rights Reserved.
#
# This file is part of TweeboParser 1.0.
#
# TweeboParser 1.0 is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TweeboParser 1.0 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with TweeboParser 1.0.  If not, see <http://www.gnu.org/licenses/>.


# This script runs the whole pipeline of TweeboParser. It reads from a raw text input
# and produce the CoNLL format dependency parses as its output (It calls all necessary
# component, such as POS tagger, along the way).

# Get the path of the components of TweeboParser

# To run the parser:

if [ "$#" -ne 4 ]; then
    echo "Usage: ./tweeboparser_runner.sh [path_to_tweeboparser] [path_to_raw_input_file_one_sentence_a_line] [working_directory_name] [output_file_name]"
else

# Starting point:
# -- Raw text tweets, one line per tweet.
ROOT_DIR=$1
INPUT_FILE=$2
WORKING_DIR=$3
OUTPUT_FILE_NAME=$4

SCRIPT_DIR="${ROOT_DIR}/scripts"
TAGGER_DIR="${ROOT_DIR}/ark-tweet-nlp-0.3.2"
PARSER_DIR="${ROOT_DIR}/TBParser"
TOKENSEL_DIR="${ROOT_DIR}/token_selection"
MODEL_DIR="${ROOT_DIR}/pretrained_models"


# --> Run Twitter POS tagger on top of it. (Tokenization and Converting to CoNLL format along the way.)
${SCRIPT_DIR}/tokenize_and_tag.sh ${ROOT_DIR} ${TAGGER_DIR} ${WORKING_DIR} ${MODEL_DIR} ${SCRIPT_DIR} ${INPUT_FILE}

echo "Starting dependency parsing  : step 1 of 3 : token selection"
# --> Append Brown Clusters on the end of each word.
python ${SCRIPT_DIR}/AugumentBrownClusteringFeature46.py ${MODEL_DIR}/twitter_brown_clustering_full ${WORKING_DIR}/tagger.out N > ${WORKING_DIR}/tag.br.out
rm ${WORKING_DIR}/tagger.out

# --> Run Token Selection Tool to get the token selections appended on the end of each word.
python ${TOKENSEL_DIR}/pipeline.py ${WORKING_DIR}/tag.br.out ${MODEL_DIR}/tokensel_weights > ${WORKING_DIR}/test
rm ${WORKING_DIR}/tag.br.out

# -- Start Parsing.

echo "Starting dependency parsing : step 2 of 3: actual dependency parsing (1/2)"
cd ${PARSER_DIR}
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:`pwd;`/deps/local/lib:"

# --> Parse the first time using PTB model to get the scores

rm -f -r ${WORKING_DIR}/test_score
mkdir ${WORKING_DIR}/test_score

./TurboParser --test --file_model=${MODEL_DIR}/ptb_parsing_model --file_test=${WORKING_DIR}/test --file_prediction=${WORKING_DIR}/ptb_single_predict_test --output_posterior=true --use_posterior=false --posterior_dir=${WORKING_DIR}/test_score 

echo "Starting dependency parsing : step 3 of 3: actual dependency parsing (2/2)"

# --> Parse the second time using PTB score as features to get the final results
./TurboParser --test --file_model=${MODEL_DIR}/parsing_model --file_test=${WORKING_DIR}/test --file_prediction=${WORKING_DIR}/test_predict --output_posterior=false --use_posterior=true --posterior_dir=${WORKING_DIR}/test_score

echo "Finished run.sh TurboParser script"

# -- Output the results.
cd ${ROOT_DIR}
cat ${WORKING_DIR}/test_predict > ${OUTPUT_FILE_NAME}

fi



