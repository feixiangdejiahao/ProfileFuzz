import os
import random
import struct
import sys


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


class GcdaConst:
    GCOV_VERSION_3_4_0 = 0x30400
    GCOV_VERSION_3_3_0 = 0x30300

    BBG_FILE_MAGIC = b'gbbg'
    GCNO_FILE_MAGIC = b'oncg'
    GCDA_FILE_MAGIC = b'adcg'

    GCNO_FILE_MAGIC_BIGENDIAN = b'gcno'
    GCDA_FILE_MAGIC_BIGENDIAN = b'gcda'

    GCOV_TAG_FUNCTION = 0x01000000
    GCOV_TAG_BLOCKS = 0x01410000
    GCOV_TAG_ARCS = 0x01430000
    GCOV_TAG_LINES = 0x01450000
    GCOV_TAG_COUNTER_BASE = 0x01a10000
    GCOV_TAG_INTERVAL = 0x01a30000
    GCOV_TAG_POW2 = 0x01a50000
    GCOV_TAG_TOPN = 0x01a70000
    GCOV_TAG_TIME_PROFILER = 0x01af0000
    GCOV_TAG_OBJECT_SUMMARY = 0xa1000000  # Obsolete
    GCOV_TAG_PROGRAM_SUMMARY = 0xa3000000

    # GCNO_SOURCEFILE = 0x80000001
    # GCNO_FUNCTIONNAME = 0x80000002

    GCOVIO_TAGTYPE_STR = {GCOV_TAG_FUNCTION: "GCOV_TAG_FUNCTION",
                          GCOV_TAG_BLOCKS: "GCOV_TAG_BLOCKS",
                          GCOV_TAG_ARCS: "GCOV_TAG_ARCS",
                          GCOV_TAG_INTERVAL: "GCOV_TAG_INTERVAL",
                          GCOV_TAG_POW2: "GCOV_TAG_POW2",
                          GCOV_TAG_TOPN: "GCOV_TAG_TOPN",
                          GCOV_TAG_LINES: "GCOV_TAG_LINES",
                          GCOV_TAG_COUNTER_BASE: "GCOV_TAG_COUNTER_BASE",
                          GCOV_TAG_TIME_PROFILER: "GCOV_TAG_TIME_PROFILER",
                          GCOV_TAG_OBJECT_SUMMARY: "GCOV_TAG_OBJECT_SUMMARY",
                          GCOV_TAG_PROGRAM_SUMMARY: "GCOV_TAG_PROGRAM_SUMMARY"}

    PACKUINT32 = "<I"
    PACKUINT32_BIGENDIAN = ">I"

    LOWORDERMASK = 0x00000000ffffffff
    HIGHORDERMASK = 0xffffffff00000000

    GCOV_FLAG_ARC_ON_TREE = 1
    GCOV_FLAG_ARC_FAKE = 2
    GCOV_FLAG_ARC_FALLTHROUGH = 4

    GCOVIO_STRINGPADDING = ['\x00\x00\x00\x00', '\x00\x00\x00', '\x00\x00', '\x00']


class GcdaFileHeader:
    """
        uint32:magic
        uint32:version
        uint32:stamp
        uint32:unexec_blocks
    """

    def __init__(self, magic, version, stamp, cwd=None, unexec_blocks=None):
        self.magic = magic
        self.version = version
        self.stamp = stamp
        self.cwd = cwd
        self.unexec_blocks = unexec_blocks
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
        if tagKey in GcdaConst.GCOVIO_TAGTYPE_STR:
            tagType = GcdaConst.GCOVIO_TAGTYPE_STR[tagKey]
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
        self.pack_str32 = GcdaConst.PACKUINT32
        self.filename = filename
        self.header = header
        self.records = records
        return

    def mutate(self):
        """
        """
        data = [record for record in self.records if
                isinstance(record, GCovDataCounterBaseRecord) or isinstance(record, GCovDataTimeProfilerRecord)]
        record = data[random.Random().randint(0, len(data) - 1)]
        mutator = random.Random().randint(0, 3)
        if mutator == 0:
            self.extremum_mutation(record)
        elif mutator == 1:
            self.one_value_mutation(record)
        elif mutator == 2:
            self.shuffle_mutation(record)
        else:
            self.random_mutation(record)

    @staticmethod
    def extremum_mutation(record):
        if isinstance(record, GCovDataCounterBaseRecord):
            data = record.counters
        else:
            data = record.time_profiler
        if random.randint(0, 1):
            data[random.randint(0, len(data) - 1)] = 2 ** 32 - 1
        else:
            data[random.randint(0, len(data) - 1)] = 0

    @staticmethod
    def one_value_mutation(record):
        if isinstance(record, GCovDataCounterBaseRecord):
            data = record.counters
        else:
            data = record.time_profiler
        index = random.randint(0, len(data) - 1)
        if random.randint(0, 1):
            if data[index] == 2 ** 32 - 1:
                data[index] -= 1
            else:
                data[index] += 1
        else:
            if data[index] == 0:
                data[index] += 1
            else:
                data[index] -= 1
        pass

    @staticmethod
    def shuffle_mutation(record):
        if isinstance(record, GCovDataCounterBaseRecord):
            data = record.counters
        else:
            data = record.time_profiler
        random.shuffle(data)

    @staticmethod
    def random_mutation(record):
        if isinstance(record, GCovDataCounterBaseRecord):
            data = record.counters
        else:
            data = record.time_profiler
        data[random.randint(0, len(data) - 1)] = random.randint(0, 2 ** 32)

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
        print("Saved %s" % self.filename)
        return

    def _load_file_header(self, file_handle, detect_endianess):
        magic = GcdaInfo.read_quad_char(file_handle)

        if detect_endianess:
            if magic == GcdaConst.GCDA_FILE_MAGIC_BIGENDIAN:
                print("Big Endian GCDA")
                self.pack_str32 = GcdaConst.PACKUINT32_BIGENDIAN
            elif magic == GcdaConst.GCDA_FILE_MAGIC:
                print("Little Endian GCDA")

        version = GcdaInfo.read_quad_char(file_handle)
        stamp = GcdaInfo.read_uint32(file_handle)

        cwd = None
        unexc_blocks = None

        self.header = GcdaFileHeader(magic, version, stamp, cwd=cwd, unexec_blocks=unexc_blocks)

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

        GcdaInfo.write_quad_char(file_handle, magic)
        GcdaInfo.write_quad_char(file_handle, version)
        GcdaInfo.write_uint32(file_handle, stamp)

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

        return quadByte

    @staticmethod
    def read_uint32(file_handle, packStr=GcdaConst.PACKUINT32):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        quadByte = file_handle.read(4)
        if len(quadByte) < 4:
            print("ERROR: Problem reading UInt32, not enough bytes left in record. quadByte=%s" % quadByte)

        val, = struct.unpack(packStr, quadByte)

        return val

    @staticmethod
    def read_uint64(file_handle, packStr=GcdaConst.PACKUINT32):
        """
            uint64:  uint32:low uint32:high
        """
        lowOrder = GcdaInfo.read_uint32(file_handle, packStr)
        highOrder = GcdaInfo.read_uint32(file_handle, packStr)

        val = (highOrder << 32) | lowOrder

        return val

    @staticmethod
    def read_string(file_handle, packStr=GcdaConst.PACKUINT32):
        """
            string: uint32:0 | uint32:length char* char:0 padding
            padding: | char:0 | char:0 char:0 | char:0 char:0 char:0
        """

        wordLength = GcdaInfo.read_uint32(file_handle, packStr)
        strLen = wordLength * 4

        strVal = file_handle.read(strLen).rstrip(b"\0")

        return strVal

    @staticmethod
    def read_record(file_handle, packStr=GcdaConst.PACKUINT32):
        """
            record: header data
            header: uint32:tag uint32:length
              data: item*
        """
        record_tag = GcdaInfo.read_uint32(file_handle, packStr)
        record_length = GcdaInfo.read_uint32(file_handle, packStr)
        # Convert to hexadecimal
        hex_str = format(record_length, '08X')

        if record_tag == GcdaConst.GCOV_TAG_COUNTER_BASE or record_tag == GcdaConst.GCOV_TAG_TIME_PROFILER or record_tag == GcdaConst.GCOV_TAG_INTERVAL or record_tag == GcdaConst.GCOV_TAG_POW2:
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
    def unpack_uint32(buffer, pos, packStr=GcdaConst.PACKUINT32):

        # Note: The comma is important because the return type from struct.unpack_from is a tuple
        val, = struct.unpack_from(packStr, buffer, pos)
        cpos = pos + 4
        return val, cpos

    @staticmethod
    def unpack_uint64(buffer, pos, packStr=GcdaConst.PACKUINT32):

        cpos = pos

        # Note: The comma is important because the return type from struct.unpack_from is a tuple
        lowOrder, = struct.unpack_from(packStr, buffer, cpos)
        cpos = cpos + 4

        highOrder, = struct.unpack_from(packStr, buffer, cpos)
        cpos = cpos + 4

        val = (highOrder << 32) | lowOrder

        return val, cpos

    @staticmethod
    def unpack_string(buffer, pos, packStr=GcdaConst.PACKUINT32):
        """
        """
        # Note: The comma is important because the return type from struct.unpack_from is a tuple
        strWords, = struct.unpack_from(packStr, buffer, pos)
        cpos = pos + 4

        val = None

        if strWords > 0:
            strlen = strWords * 4
            strend = cpos + strlen

            buffSlice = buffer[cpos: strend]
            val = buffSlice.rstrip(b'\x00').decode()

            cpos = cpos + strlen

        return val, cpos

    @staticmethod
    def write_quad_char(file_handle, quad_char):
        """
            uint32 in quad char format
        """
        file_handle.write(quad_char)
        return

    @staticmethod
    def write_uint32(file_handle, val, packStr=GcdaConst.PACKUINT32):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        file_handle.write(struct.pack(packStr, val))
        return

    @staticmethod
    def write_uint64(file_handle, val):
        """
            uint64:  uint32:low uint32:high
        """
        lowOrder = val & GcdaConst.LOWORDERMASK
        highOrder = (val & GcdaConst.HIGHORDERMASK) >> 32

        # Write the low order word
        GcdaInfo.write_uint32(file_handle, lowOrder)

        # Write the high order word
        GcdaInfo.write_uint32(file_handle, highOrder)
        return

    @staticmethod
    def write_string(file_handle, val):
        """
            string: uint32:0 | uint32:length char* char:0 padding
            padding: | char:0 | char:0 char:0 | char:0 char:0 char:0
        """
        valLen = len(val)
        padlen = valLen % 4

        file_handle.write(val)

        if (val[valLen - 1] == 'x00') and (padlen == 0):
            return

        file_handle.write(GcdaConst.GCOVIO_STRINGPADDING[padlen])

        return

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
    def unpack_record(record, packStr=GcdaConst.PACKUINT32):
        cpos = 0

        tag = record.header.tag
        header = record.header
        buffer = record.items_data

        if tag == GcdaConst.GCOV_TAG_FUNCTION:
            swap_record = GcdaInfo.unpack_function_announcement(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_COUNTER_BASE:
            swap_record = GcdaInfo.unpack_counter_base(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_INTERVAL:
            swap_record = GcdaInfo.unpack_interval(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_POW2:
            swap_record = GcdaInfo.unpack_pow2(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_TOPN:
            swap_record = GcdaInfo.unpack_topn(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_TIME_PROFILER:
            swap_record = GcdaInfo.unpack_time_profiler(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_OBJECT_SUMMARY:
            swap_record = GcdaInfo.unpack_object_summary(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_PROGRAM_SUMMARY:
            swap_record = GcdaInfo.unpack_program_summary(header, buffer, cpos, packStr)
        else:
            raise IOError("Un-recognized tag (0x%x) found at record index in file." % tag)

        return swap_record

    @staticmethod
    def unpack_object_summary(header, buffer, pos, packStr=GcdaConst.PACKUINT32):
        """
        """
        cpos = pos

        runs, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)
        summax, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)

        rval = GCovDataObjectSummaryRecord(header, runs, summax)

        return rval

    @staticmethod
    def unpack_program_summary(header, buffer, pos, packStr=GcdaConst.PACKUINT32):
        """
        """
        cpos = pos

        checksum, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)
        counts, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)
        runs, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)
        sum_all, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
        run_max, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
        sum_max, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)

        rval = GCovDataProgramSummaryRecord(header, checksum, counts, runs, sum_all, run_max, sum_max)

        return rval

    @staticmethod
    def unpack_counter_base(header, buffer, pos, packStr=GcdaConst.PACKUINT32):
        """
            announce_function: header uint32:ident uint32:checksum string:name string:source uint32:lineno
        """
        cpos = pos

        counterLength = header.length / 2
        counterIndex = 0

        counters = []

        while counterIndex < counterLength:
            nextValue, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
            if nextValue == 386547056640:
                pass
            counters.append(nextValue)
            counterIndex += 1

        rval = GCovDataCounterBaseRecord(header, counters)

        return rval

    @staticmethod
    def unpack_function_announcement(header, buffer, pos, packStr=GcdaConst.PACKUINT32):
        """
            announce_function: header uint32:ident uint32:checksum string:name string:source uint32:lineno
        """
        cpos = pos
        ident, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)
        lineno_checksum, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)
        cfg_checksum, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)

        rval = GCovDataFunctionAnnouncementRecord(header, ident, lineno_checksum, cfg_checksum)

        return rval

    @classmethod
    def unpack_time_profiler(cls, header, buffer, pos, packStr):
        cpos = pos

        counterLength = header.length / 2
        counterIndex = 0

        counters = []

        while counterIndex < counterLength:
            nextValue, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
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

        GcdaInfo.write_uint32(file_handle, header.tag)
        GcdaInfo.write_uint32(file_handle, header.length)
        GcdaInfo.write_uint32(file_handle, checksum)
        GcdaInfo.write_uint32(file_handle, counts)
        GcdaInfo.write_uint32(file_handle, runs)
        GcdaInfo.write_uint64(file_handle, sum_all)
        GcdaInfo.write_uint64(file_handle, run_max)
        GcdaInfo.write_uint64(file_handle, sum_max)

        return

    @classmethod
    def write_counter_base(cls, file_handle, record):
        header = record.header
        counters = record.counters
        if len(counters) != 0 and all(x == 0 for x in counters):
            GcdaInfo.write_uint32(file_handle, header.tag)
            GcdaInfo.write_uint32(file_handle, -header.length + 2 ** 32)
        else:
            GcdaInfo.write_uint32(file_handle, header.tag)
            GcdaInfo.write_uint32(file_handle, header.length)
            for counter in counters:
                GcdaInfo.write_uint64(file_handle, counter)
        return

    @classmethod
    def write_time_profiler(cls, file_handle, record):
        header = record.header
        time_profiler = record.time_profiler

        if all(x == 0 for x in time_profiler):
            GcdaInfo.write_uint32(file_handle, header.tag)
            GcdaInfo.write_uint32(file_handle, -header.length + 2 ** 32)
        else:
            GcdaInfo.write_uint32(file_handle, header.tag)
            GcdaInfo.write_uint32(file_handle, header.length)
            for counter in time_profiler:
                GcdaInfo.write_uint64(file_handle, counter)
        return

    @classmethod
    def write_object_summary(cls, file_handle, record):
        header = record.header
        runs = record.runs
        summax = record.sum_max

        GcdaInfo.write_uint32(file_handle, header.tag)
        GcdaInfo.write_uint32(file_handle, header.length)
        GcdaInfo.write_uint32(file_handle, runs)
        GcdaInfo.write_uint32(file_handle, summax)
        return

    @classmethod
    def write_function_announcement(cls, file_handle, record):
        header = record.header
        indent = record.ident
        lineno_checksum = record.lineno_checksum
        cfg_checksum = record.cfg_checksum

        GcdaInfo.write_uint32(file_handle, header.tag)
        GcdaInfo.write_uint32(file_handle, header.length)
        GcdaInfo.write_uint32(file_handle, indent)
        GcdaInfo.write_uint32(file_handle, lineno_checksum)
        GcdaInfo.write_uint32(file_handle, cfg_checksum)
        return

    @classmethod
    def unpack_interval(cls, header, buffer, pos, packStr):
        cpos = pos

        counterLength = header.length / 2
        counterIndex = 0

        counters = []

        while counterIndex < counterLength:
            nextValue, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
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
            nextValue, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
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
            nextValue, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
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
            GcdaInfo.write_uint32(file_handle, header.tag)
            GcdaInfo.write_uint32(file_handle, -header.length + 2 ** 32)
        else:
            GcdaInfo.write_uint32(file_handle, header.tag)
            GcdaInfo.write_uint32(file_handle, header.length)
            for counter in interval:
                GcdaInfo.write_uint64(file_handle, counter)
        return

    @classmethod
    def write_pow2(cls, file_handle, record):
        header = record.header
        pow2 = record.pow2

        if len(pow2) != 0 and all(x == 0 for x in pow2):
            GcdaInfo.write_uint32(file_handle, header.tag)
            GcdaInfo.write_uint32(file_handle, -header.length + 2 ** 32)
        else:
            GcdaInfo.write_uint32(file_handle, header.tag)
            GcdaInfo.write_uint32(file_handle, header.length)
            for counter in pow2:
                GcdaInfo.write_uint64(file_handle, counter)
        return

    @classmethod
    def write_topn(cls, file_handle, record):
        header = record.header
        topn = record.topn

        GcdaInfo.write_uint32(file_handle, header.tag)
        GcdaInfo.write_uint32(file_handle, header.length)
        for counter in topn:
            GcdaInfo.write_uint64(file_handle, counter)
