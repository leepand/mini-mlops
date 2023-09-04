import os
import re
import time


class FileReader(object):
    """
    this class is used to read file incremental
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.pos = 0

    def read(self, max_read_size=None):
        """
        read from last position

        :param max_read_size:
            maximum reading length
        :return:
            content read
        """
        # whether the file exist
        if not os.path.isfile(self.file_path):
            return ""
        ret = ""
        with open(self.file_path) as fp:
            fp.seek(0, os.SEEK_END)
            size = fp.tell()
            if size >= self.pos:
                fp.seek(self.pos, os.SEEK_SET)
                if (max_read_size is None) or (max_read_size > (size - self.pos)):
                    max_read_size = size - self.pos
                ret = fp.read(max_read_size)
                self.pos = self.pos + len(ret)
            else:  # may be a new file with the same name
                fp.seek(0, os.SEEK_SET)
                if (max_read_size is None) or (max_read_size > size):
                    max_read_size = size
                ret = fp.read(max_read_size)
                self.pos = len(ret)
        return ret


def __check_reg_str_contain(file_reader, reg_str):
    """
    check if any line matches the reg_str

    :param file_reader:
        FileReade Object
    :return:
        return True if found
    """
    file_content = file_reader.read()
    lines = file_content.splitlines()
    for line in lines:
        if re.search(reg_str, line):
            return True
    return False


def wait_until_reg_str_exist(dst_file_path, reg_str, max_wait_sec=10, interval_sec=0.5):
    """
    wait until any line in the file matches the \
    reg_str(regular expression string)

    :param dst_file_path:
        searching path
    :param reg_str:
        regular expression string
    :param max_wait_sec:
        maximum waiting time until timeout
    :param interval_sec:
        state check interval
    :return:
        True if found
    """
    curr_wait_sec = 0
    file_reader = FileReader(dst_file_path)
    while curr_wait_sec < max_wait_sec:
        if __check_reg_str_contain(file_reader, reg_str):
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


# dst_file_path="logs.log"
# file_reader = FileReader(dst_file_path)
# reg_str="Starting gunicorn1"
# __check_reg_str_contain(file_reader, reg_str)
