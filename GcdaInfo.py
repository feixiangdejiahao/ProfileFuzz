import os
import random

import GcovConst
from GcovIO import GcovIO


class GCovDataFunctionAnnouncementRecord:
    """
        header uint32:ident uint32:checksum
    """

    def __init__(self, header, ident, lineno_checksum, cfg_checksum):
        self.header = header
        self.ident = ident
        self.lineno_checksum = lineno_checksum
        self.cfg_checksum = cfg_checksum
        return


class GCovDataCounterBaseRecord:
    """
    """

    def __init__(self, header, counters):
        self.header = header
        self.counters = counters


class GCovDataObjectSummaryRecord:
    """"""

    def __init__(self, header, runs, summax):
        self.header = header
        self.runs = runs
        self.sum_max = summax
        return


class GCovDataProgramSummaryRecord:
    """"""

    def __init__(self, header, checksum, counts, runs, sum_all, run_max, sum_max):
        self.header = header
        self.check_sum = checksum
        self.counts = counts
        self.runs = runs
        self.sum_all = sum_all
        self.run_max = run_max
        self.sum_max = sum_max
        return


class GcdaFileHeader:
    """
        uint32:magic
        uint32:version
        uint32:stamp
        uint32:unexec_blocks
    """

    def __init__(self, magic, version, stamp):
        self.magic = magic
        self.version = version
        self.stamp = stamp
        return


class GcdaRecordHeader:
    """
        uint32:tag uint32:length
    """

    def __init__(self, tag, length):
        self.tag = tag
        self.length = length
        return


class GcdaRecord:
    """
        A gcov record consists of a header followed by a data buffer.  The head contains a
        tag and length member.  The tag indicates the type of record and the length indicates
        the size of the buffer in 4 byte words.

             Record => [Header] [Buffer]

             Header => [UInt32: Tag] [UInt32: Length]

             Buffer => [Items]*

        The buffer in a gcov record is composed of items.  The items are grouped in various ways
        they are of three basic types.

             UInt32 (stored in the endieness of the host machine)
             UInt64 => [UInt32 (low)] [UInt32 (high)]
             String => [Length] [CharBuffer]

        Strings for a gcov record are padded using from 1 to 4 bytes of padding to ensure the
        string length ends on a 32bit word boundry.  A null string is represented as a string with
        a length of 0 and no buffer and therefore no padding.

            NullString => [Length: 0]
    """

    def __init__(self, tag, length, items_data):
        self.header = GcdaRecordHeader(tag, length)
        self.items_data = items_data
        return

    def __str__(self):
        tagKey = self.header.tag
        tagType = str(tagKey)
        if tagKey in GcovConst.GCOVIO_TAGTYPE_STR:
            tagType = GcovConst.GCOVIO_TAGTYPE_STR[tagKey]
        strval = "Type=%s Length=%d Data=%r" % (tagType, self.header.length, self.items_data)
        return strval


class GCovDataTimeProfilerRecord:
    def __init__(self, header, time_profiler):
        self.header = header
        self.time_profiler = time_profiler


class GCovDataIntervalRecord:
    def __init__(self, header, interval):
        self.header = header
        self.interval = interval


class GCovDataPow2Record:
    def __init__(self, header, pow2):
        self.header = header
        self.pow2 = pow2


class GCovDatTopnRecord:
    def __init__(self, header, topn):
        self.header = header
        self.topn = topn


class GcdaInfo:
    """
        FILE FORMAT:

        == Header ==
        [Magic] + [Version] + [Stamp] + [Records*]

        == Records ==
        [RecordHeader] + [RecordData]

        == RecordHeader ==
        [Tag(UInt32)] + [Length(UInt32)]

        Note: Length is the number of 4 byte words that are stored in the record

        == RecordData ==
        [Items*]

        == Items ==
            [UInt32] | [Int64] | [String]

        UInt32: byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        UInt64: low (UInt32) high (UInt32)
        String: UInt32:0 | UInt32:length + char* char:0 padding

        Padding: '' | 'x00' | 'x00x00' | 'x00x00x00'
    """

    def __init__(self, filename=None, header=None, records=None):
        self.source_file_name = None
        self.file_path = None
        self.pack_str32 = GcovConst.PACKUINT32
        self.filename = filename
        self.header = header
        self.records = records
        return


    def pull_records(self):
        """
        """
        record_count = len(self.records)
        rindex = 0

        while rindex < record_count:
            self.pull_record_at_index(rindex)
            rindex += 1

    def pull_record_at_index(self, index):
        """
        """
        if self.records is None:
            raise LookupError(
                "GCovDataFile.pull_record_at_index: You must call GCovDataFile.Load before attempting to pull a record.")

        rec_count = len(self.records)
        if index >= rec_count:
            raise IndexError("GCovDataFile.pull_record_at_index: The specified index was out of range.")

        record = self.records[index]
        if isinstance(record, GcdaRecord):
            swap_record = GcdaInfo.unpack_record(record, self.pack_str32)

            self.records[index] = swap_record
            del record
            record = swap_record

        return record

    def load(self, filename=None, detectEndianess=True):
        if filename is not None:
            self.filename = filename
            self.file_path = os.path.dirname(filename)
            self.source_file_name = os.path.basename(filename).split('_')[0]

        if self.filename is None:
            raise IOError("GCovIO: load 'Filename' not set")

        file_handle = None

        try:
            file_handle = open(self.filename, 'rb')

            file_size = os.fstat(file_handle.fileno()).st_size

            self._load_file_header(file_handle, detectEndianess)
            self._load_records(file_handle, file_size)
        finally:
            if file_handle is not None:
                file_handle.close()
        return

    def save(self, filename=None):
        if filename is not None:
            self.filename = filename

        if self.filename is None:
            raise IOError("GCovInfo: save 'Filename' not set")

        try:
            file_handle = open(self.filename, 'wb')

            self._save_header(file_handle)
            self._save_records(file_handle)
        finally:
            if file_handle is not None:
                file_handle.close()
        # print("Saved %s" % self.filename)
        return

    def _load_file_header(self, file_handle, detect_endianess):
        magic = GcovIO.read_quad_char(file_handle)

        if detect_endianess:
            if magic == GcovConst.GCDA_FILE_MAGIC_BIGENDIAN:
                print("Big Endian GCDA")
                self.pack_str32 = GcovConst.PACKUINT32_BIGENDIAN
            elif magic == GcovConst.GCDA_FILE_MAGIC:
                print("Little Endian GCDA")

        version = GcovIO.read_quad_char(file_handle)
        stamp = GcovIO.read_uint32(file_handle)

        self.header = GcdaFileHeader(magic, version, stamp)

        return

    def _load_records(self, file_handle, file_size):
        self.records = []

        cur_pos = file_handle.tell()

        while cur_pos < file_size:

            bytes_remaining = file_size - cur_pos
            if bytes_remaining < 8:
                print("Reached the end of file without enough bytes remaining to read a complete record.")
                print("filename=%s" % self.filename)
                print("bytesRemaining=%d" % bytes_remaining)

                extra_buffer = file_handle.read(bytes_remaining)
                extra_bytes = ""

                for byte in extra_buffer:
                    extra_bytes += "0x%x " % byte

                print("extraBytes=%s" % extra_bytes)

                break

            nxtRecord = GcdaInfo.read_record(file_handle)

            if nxtRecord is None:
                break

            self.records.append(nxtRecord)

            cur_pos = file_handle.tell()

        return

    def _save_header(self, file_handle):

        magic = self.header.magic
        version = self.header.version
        stamp = self.header.stamp

        GcovIO.write_quad_char(file_handle, magic)
        GcovIO.write_quad_char(file_handle, version)
        GcovIO.write_uint32(file_handle, stamp)

        return

    def _save_records(self, file_handle):

        for record in self.records:
            GcdaInfo.write_record(file_handle, record)

    @staticmethod
    def read_quad_char(file_handle):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        quadByte = file_handle.read(4)
        if len(quadByte) < 4:
            print("ERROR: Problem reading UInt32, not enough bytes left in record. quadByte=%s" % quadByte)

    @staticmethod
    def read_record(file_handle, packStr=GcovConst.PACKUINT32):
        """
            record: header data
            header: uint32:tag uint32:length
              data: item*
        """
        record_tag = GcovIO.read_uint32(file_handle, packStr)
        record_length = GcovIO.read_uint32(file_handle, packStr)
        # Convert to hexadecimal
        hex_str = format(record_length, '08X')

        if record_tag == GcovConst.GCOV_TAG_COUNTER_BASE or record_tag == GcovConst.GCOV_TAG_TIME_PROFILER or record_tag == GcovConst.GCOV_TAG_INTERVAL or record_tag == GcovConst.GCOV_TAG_POW2:
            if hex_str[0] in "89ABCDEF":
                # If it corresponds to a negative signed integer
                record_length = abs(int(hex_str, 16) - 2 ** 32)
                byte_len = record_length * 4
                record_items_data = b'\x00' * byte_len
            else:
                # Otherwise, it's a positive signed integer
                record_length = int(hex_str, 16)
                byte_len = record_length * 4
                record_items_data = file_handle.read(byte_len)
        else:
            record_length = int(hex_str, 16)
            byte_len = record_length * 4
            record_items_data = file_handle.read(byte_len)

        return GcdaRecord(record_tag, record_length, record_items_data)

    @staticmethod
    def write_record(file_handle, record):
        """
            record: header data
            header: uint32:tag uint32:length
              data: item*
        """
        if isinstance(record, GCovDataProgramSummaryRecord):
            GcdaInfo.write_program_summary(file_handle, record)
        elif isinstance(record, GCovDataCounterBaseRecord):
            GcdaInfo.write_counter_base(file_handle, record)
        elif isinstance(record, GCovDataIntervalRecord):
            GcdaInfo.write_interval(file_handle, record)
        elif isinstance(record, GCovDataPow2Record):
            GcdaInfo.write_pow2(file_handle, record)
        elif isinstance(record, GCovDatTopnRecord):
            GcdaInfo.write_topn(file_handle, record)
        elif isinstance(record, GCovDataTimeProfilerRecord):
            GcdaInfo.write_time_profiler(file_handle, record)
        elif isinstance(record, GCovDataObjectSummaryRecord):
            GcdaInfo.write_object_summary(file_handle, record)
        elif isinstance(record, GCovDataFunctionAnnouncementRecord):
            GcdaInfo.write_function_announcement(file_handle, record)
        return

    @staticmethod
    def unpack_record(record, packStr=GcovConst.PACKUINT32):
        cpos = 0

        tag = record.header.tag
        header = record.header
        buffer = record.items_data

        if tag == GcovConst.GCOV_TAG_FUNCTION:
            swap_record = GcdaInfo.unpack_function_announcement(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_COUNTER_BASE:
            swap_record = GcdaInfo.unpack_counter_base(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_INTERVAL:
            swap_record = GcdaInfo.unpack_interval(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_POW2:
            swap_record = GcdaInfo.unpack_pow2(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_TOPN:
            swap_record = GcdaInfo.unpack_topn(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_TIME_PROFILER:
            swap_record = GcdaInfo.unpack_time_profiler(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_OBJECT_SUMMARY:
            swap_record = GcdaInfo.unpack_object_summary(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_PROGRAM_SUMMARY:
            swap_record = GcdaInfo.unpack_program_summary(header, buffer, cpos, packStr)
        else:
            raise IOError("Un-recognized tag (0x%x) found at record index in file." % tag)

        return swap_record

    @staticmethod
    def unpack_object_summary(header, buffer, pos, packStr=GcovConst.PACKUINT32):
        """
        """
        cpos = pos

        runs, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        summax, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)

        rval = GCovDataObjectSummaryRecord(header, runs, summax)

        return rval

    @staticmethod
    def unpack_program_summary(header, buffer, pos, packStr=GcovConst.PACKUINT32):
        """
        """
        cpos = pos

        checksum, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        counts, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        runs, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        sum_all, cpos = GcovIO.unpack_uint64(buffer, cpos, packStr)
        run_max, cpos = GcovIO.unpack_uint64(buffer, cpos, packStr)
        sum_max, cpos = GcovIO.unpack_uint64(buffer, cpos, packStr)

        rval = GCovDataProgramSummaryRecord(header, checksum, counts, runs, sum_all, run_max, sum_max)

        return rval

    @staticmethod
    def unpack_counter_base(header, buffer, pos, packStr=GcovConst.PACKUINT32):
        """
            announce_function: header uint32:ident uint32:checksum string:name string:source uint32:lineno
        """
        cpos = pos

        counterLength = header.length / 2
        counterIndex = 0

        counters = []

        while counterIndex < counterLength:
            nextValue, cpos = GcovIO.unpack_uint64(buffer, cpos, packStr)
            if nextValue == 386547056640:
                pass
            counters.append(nextValue)
            counterIndex += 1

        rval = GCovDataCounterBaseRecord(header, counters)

        return rval

    @staticmethod
    def unpack_function_announcement(header, buffer, pos, packStr=GcovConst.PACKUINT32):
        """
            announce_function: header uint32:ident uint32:checksum string:name string:source uint32:lineno
        """
        cpos = pos
        ident, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        lineno_checksum, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)

        cfg_checksum, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)

        rval = GCovDataFunctionAnnouncementRecord(header, ident, lineno_checksum, cfg_checksum)

        return rval

    @classmethod
    def unpack_time_profiler(cls, header, buffer, pos, packStr):
        cpos = pos

        counterLength = header.length / 2
        counterIndex = 0

        counters = []

        while counterIndex < counterLength:
            nextValue, cpos = GcovIO.unpack_uint64(buffer, cpos, packStr)
            if nextValue == 386547056640:
                pass
            counters.append(nextValue)
            counterIndex += 1

        rval = GCovDataTimeProfilerRecord(header, counters)

        return rval

    @classmethod
    def write_program_summary(cls, file_handle, record):
        header = record.header
        checksum = record.check_sum
        counts = record.counts
        runs = record.runs
        sum_all = record.sum_all
        run_max = record.run_max
        sum_max = record.sum_max

        GcovIO.write_uint32(file_handle, header.tag)
        GcovIO.write_uint32(file_handle, header.length)
        GcovIO.write_uint32(file_handle, checksum)
        GcovIO.write_uint32(file_handle, counts)
        GcovIO.write_uint32(file_handle, runs)
        GcovIO.write_uint64(file_handle, sum_all)
        GcovIO.write_uint64(file_handle, run_max)
        GcovIO.write_uint64(file_handle, sum_max)

        return

    @classmethod
    def write_counter_base(cls, file_handle, record):
        header = record.header
        counters = record.counters
        if len(counters) != 0 and all(x == 0 for x in counters):
            GcovIO.write_uint32(file_handle, header.tag)
            GcovIO.write_uint32(file_handle, -header.length + 2 ** 32)
        else:
            GcovIO.write_uint32(file_handle, header.tag)
            GcovIO.write_uint32(file_handle, header.length)
            for counter in counters:
                GcovIO.write_uint64(file_handle, counter)
        return

    @classmethod
    def write_time_profiler(cls, file_handle, record):
        header = record.header
        time_profiler = record.time_profiler

        if all(x == 0 for x in time_profiler):
            GcovIO.write_uint32(file_handle, header.tag)
            GcovIO.write_uint32(file_handle, -header.length + 2 ** 32)
        else:
            GcovIO.write_uint32(file_handle, header.tag)
            GcovIO.write_uint32(file_handle, header.length)
            for counter in time_profiler:
                GcovIO.write_uint64(file_handle, counter)
        return

    @classmethod
    def write_object_summary(cls, file_handle, record):
        header = record.header
        runs = record.runs
        summax = record.sum_max

        GcovIO.write_uint32(file_handle, header.tag)
        GcovIO.write_uint32(file_handle, header.length)
        GcovIO.write_uint32(file_handle, runs)
        GcovIO.write_uint32(file_handle, summax)
        return

    @classmethod
    def write_function_announcement(cls, file_handle, record):
        header = record.header
        indent = record.ident
        lineno_checksum = record.lineno_checksum
        cfg_checksum = record.cfg_checksum

        GcovIO.write_uint32(file_handle, header.tag)
        GcovIO.write_uint32(file_handle, header.length)
        GcovIO.write_uint32(file_handle, indent)
        GcovIO.write_uint32(file_handle, lineno_checksum)
        GcovIO.write_uint32(file_handle, cfg_checksum)
        return

    @classmethod
    def unpack_interval(cls, header, buffer, pos, packStr):
        cpos = pos

        counterLength = header.length / 2
        counterIndex = 0

        counters = []

        while counterIndex < counterLength:
            nextValue, cpos = GcovIO.unpack_uint64(buffer, cpos, packStr)
            if nextValue == 386547056640:
                pass
            counters.append(nextValue)
            counterIndex += 1

        rval = GCovDataIntervalRecord(header, counters)

        return rval

    @classmethod
    def unpack_pow2(cls, header, buffer, pos, packStr):
        cpos = pos

        counterLength = header.length / 2
        counterIndex = 0

        counters = []

        while counterIndex < counterLength:
            nextValue, cpos = GcovIO.unpack_uint64(buffer, cpos, packStr)
            if nextValue == 386547056640:
                pass
            counters.append(nextValue)
            counterIndex += 1

        rval = GCovDataPow2Record(header, counters)

        return rval

    @classmethod
    def unpack_topn(cls, header, buffer, pos, packStr):
        cpos = pos

        counterLength = header.length / 2
        counterIndex = 0

        counters = []

        while counterIndex < counterLength:
            nextValue, cpos = GcovIO.unpack_uint64(buffer, cpos, packStr)
            if nextValue == 386547056640:
                pass
            counters.append(nextValue)
            counterIndex += 1

        rval = GCovDatTopnRecord(header, counters)

        return rval

    @classmethod
    def write_interval(cls, file_handle, record):
        header = record.header
        interval = record.interval

        if len(interval) != 0 and all(x == 0 for x in interval):
            GcovIO.write_uint32(file_handle, header.tag)
            GcovIO.write_uint32(file_handle, -header.length + 2 ** 32)
        else:
            GcovIO.write_uint32(file_handle, header.tag)
            GcovIO.write_uint32(file_handle, header.length)
            for counter in interval:
                GcovIO.write_uint64(file_handle, counter)
        return

    @classmethod
    def write_pow2(cls, file_handle, record):
        header = record.header
        pow2 = record.pow2

        if len(pow2) != 0 and all(x == 0 for x in pow2):
            GcovIO.write_uint32(file_handle, header.tag)
            GcovIO.write_uint32(file_handle, -header.length + 2 ** 32)
        else:
            GcovIO.write_uint32(file_handle, header.tag)
            GcovIO.write_uint32(file_handle, header.length)
            for counter in pow2:
                GcovIO.write_uint64(file_handle, counter)
        return

    @classmethod
    def write_topn(cls, file_handle, record):
        header = record.header
        topn = record.topn

        GcovIO.write_uint32(file_handle, header.tag)
        GcovIO.write_uint32(file_handle, header.length)
        for counter in topn:
            GcovIO.write_uint64(file_handle, counter)
