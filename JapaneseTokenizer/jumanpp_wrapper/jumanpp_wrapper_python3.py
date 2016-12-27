from pyknp import Jumanpp
from pyknp import MList
from JapaneseTokenizer.object_models import WrapperBase
from JapaneseTokenizer.common import text_preprocess, filter, juman_utils
from JapaneseTokenizer import init_logger
from JapaneseTokenizer.datamodels import FilteredObject, TokenizedSenetence
from typing import List, Dict, Tuple, Union, TypeVar
import logging
import sys
import socket
import six
import os
import re
__author__ = 'kensuke-mi'

logger = init_logger.init_logger(logging.getLogger(init_logger.LOGGER_NAME))
python_version = sys.version_info
ContentsTypes = TypeVar('T')

try:
    import pyknp
except ImportError:
    logger.error(msg='pyknp is not ready to use. Check your installing log.')


class JumanppClient(object):
    """Class for receiving data as client"""
    def __init__(self, hostname:str, port:int, option=None):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((hostname, port))
        except ConnectionRefusedError:
            raise Exception("There is no jumanpp server hostname={}, port={}".format(hostname, port))
        except:
            raise
        if option is not None:
            self.sock.send(option)
        data = b""

    def __del__(self):
        if self.sock: self.sock.close()

    def query(self, sentence, pattern):
        assert (isinstance(sentence, six.text_type))
        self.sock.sendall(b"%s\n" % sentence.encode('utf-8').strip())
        data = self.sock.recv(1024)
        assert isinstance(data, bytes)
        recv = data
        while not re.search(pattern, recv):
            data = self.sock.recv(1024)
            recv = b"%s%s" % (recv, data)
        return recv.strip().decode('utf-8')


class JumanppWrapper(WrapperBase):
    """Class for Juman++"""
    def __init__(self, command='jumanpp', timeout=30, pattern=r'EOS', server:str=None, port:int=12000, **args):
        # type: (str, int, str, str) -> None
        if not server is None:
            pattern = pattern.encode('utf-8')


        self.eos_pattern = pattern
        if server is None:
            self.jumanpp_obj = Jumanpp(
                command=command,
                timeout=timeout,
                pattern=pattern,
                **args)
        else:
            self.jumanpp_obj = JumanppClient(hostname=server, port=port)

    def tokenize(self, sentence, normalize=True, is_feature=False, is_surface=False, return_list=True):
        # type: (str, bool, bool, bool, bool)
        """* What you can do
        -
        """
        if normalize:
            normalized_sentence = text_preprocess.normalize_text(sentence, dictionary_mode='ipadic')
        else:
            normalized_sentence = sentence

        if isinstance(self.jumanpp_obj, Jumanpp):
            ml_token_object = self.jumanpp_obj.analysis(input_str=normalized_sentence)
        elif isinstance(self.jumanpp_obj, JumanppClient):
            server_response = self.jumanpp_obj.query(sentence=normalized_sentence, pattern=self.eos_pattern)
            ml_token_object = MList(server_response)
        else:
            raise Exception('Not defined')

        token_objects = [
            juman_utils.extract_morphological_information(
                mrph_object=morph_object,
                is_surface=is_surface,
                is_feature=is_feature
            )
            for morph_object in ml_token_object]

        if return_list:
            tokenized_objects = TokenizedSenetence(
                sentence=sentence,
                tokenized_objects=token_objects)
            return tokenized_objects.convert_list_object()
        else:
            tokenized_objects = TokenizedSenetence(
                sentence=sentence,
                tokenized_objects=token_objects)
            return tokenized_objects

    def convert_str(self, p_c_tuple):
        converted = []
        for item in p_c_tuple:
            if isinstance(item, str):
                converted.append(item)
            else:
                converted.append(item)
        return converted

    def __check_pos_condition_str(self, pos_condistion):
        assert isinstance(pos_condistion, list)
        # [ ('', '', '') ]

        return [
            tuple(self.convert_str(p_c_tuple))
            for p_c_tuple
            in pos_condistion
            ]

    def filter(self, parsed_sentence: TokenizedSenetence, pos_condition=None, stopwords=None) -> FilteredObject:
        assert isinstance(parsed_sentence, TokenizedSenetence)
        assert isinstance(pos_condition, (type(None), list))
        assert isinstance(stopwords, (type(None), list))

        if isinstance(stopwords, type(None)):
            s_words = []
        else:
            s_words = stopwords

        if isinstance(pos_condition, type(None)):
            p_condition = []
        else:
            p_condition = self.__check_pos_condition_str(pos_condition)

        filtered_object = filter.filter_words(
            tokenized_obj=parsed_sentence,
            valid_pos=p_condition,
            stopwords=s_words
        )
        assert isinstance(filtered_object, FilteredObject)

        return filtered_object