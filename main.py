import os
import struct


class GCovDataFunctionAnnouncementRecord:
    """
        header uint32:ident uint32:checksum
    """

    def __init__(self, header, ident, checksum):
        self.header = header
        self.indent = ident
        self.check_sum = checksum
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

    def __init__(self, header, checksum, num, runs, sum, max, summax):
        self.header = header
        self.check_sum = checksum
        self.num = num
        self.runs = runs
        self.sum = sum
        self.max = max
        self.sum_max = summax
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
    GCOV_TAG_OBJECT_SUMMARY = 0xa1000000  # Obsolete
    GCOV_TAG_PROGRAM_SUMMARY = 0xa3000000

    # GCNO_SOURCEFILE = 0x80000001
    # GCNO_FUNCTIONNAME = 0x80000002

    GCOVIO_TAGTYPE_STR = {GCOV_TAG_FUNCTION: "GCOV_TAG_FUNCTION",
                          GCOV_TAG_BLOCKS: "GCOV_TAG_BLOCKS",
                          GCOV_TAG_ARCS: "GCOV_TAG_ARCS",
                          GCOV_TAG_LINES: "GCOV_TAG_LINES",
                          GCOV_TAG_COUNTER_BASE: "GCOV_TAG_COUNTER_BASE",
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

    def __init__(self, tag, length, itemsData):
        self.header = GcdaRecordHeader(tag, length)
        self.items_data = itemsData
        return

    def __str__(self):
        tagKey = self.header.tag
        tagType = str(tagKey)
        if tagKey in GcdaConst.GCOVIO_TAGTYPE_STR:
            tagType = GcdaConst.GCOVIO_TAGTYPE_STR[tagKey]
        strval = "Type=%s Length=%d Data=%r" % (tagType, self.header.length, self.items_data)
        return strval


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

    def pull_records(self):
        """
        """
        recordCount = len(self.records)
        rindex = 0

        while rindex < recordCount:
            self.pull_record_at_index(rindex)
            rindex += 1

    def pull_record_at_index(self, index):
        """
        """
        if self.records is None:
            raise LookupError(
                "GCovDataFile.pull_record_at_index: You must call GCovDataFile.Load before attempting to pull a record.")

        recCount = len(self.records)
        if index >= recCount:
            raise IndexError("GCovDataFile.pull_record_at_index: The specified index was out of range.")

        record = self.records[index]
        if isinstance(record, GcdaRecord):
            swapRecord = GcdaInfo.unpack_record(record, self.pack_str32)

            self.records[index] = swapRecord
            del record
            record = swapRecord

        return record

    def load(self, filename=None, detectEndianess=True):
        if filename is not None:
            self.filename = filename

        if self.filename is None:
            raise IOError("GCovIO: load 'Filename' not set")

        fileHandle = None

        try:
            fileHandle = open(self.filename, 'rb')

            fileSize = os.fstat(fileHandle.fileno()).st_size

            self._load_file_header(fileHandle, detectEndianess)
            self._load_records(fileHandle, fileSize)
        finally:
            if fileHandle is not None:
                fileHandle.close()
        return

    def save(self, filename=None):
        if filename is not None:
            self.filename = filename

        if self.filename is None:
            raise IOError("GCovInfo: save 'Filename' not set")

        try:
            fileHandle = open(self.filename, 'w')

            self._save_header(fileHandle)
            self._save_records(fileHandle)
        finally:
            if fileHandle is not None:
                fileHandle.close()

        return

    def _load_file_header(self, fileHandle, detectEndianess):
        magic = GcdaInfo.read_quad_char(fileHandle)

        if detectEndianess:
            if magic == GcdaConst.GCDA_FILE_MAGIC_BIGENDIAN:
                print("Big Endian GCDA")
                self.pack_str32 = GcdaConst.PACKUINT32_BIGENDIAN
            elif magic == GcdaConst.GCDA_FILE_MAGIC:
                print("Little Endian GCDA")

        version = GcdaInfo.read_quad_char(fileHandle)
        stamp = GcdaInfo.read_uint32(fileHandle)

        cwd = None
        unexc_blocks = None

        self.header = GcdaFileHeader(magic, version, stamp, cwd=cwd, unexec_blocks=unexc_blocks)

        return

    def _load_records(self, fileHandle, fileSize):
        self.records = []

        curPos = fileHandle.tell()

        while curPos < fileSize:

            bytesRemaining = fileSize - curPos
            if bytesRemaining < 8:
                print("Reached the end of file without enough bytes remaining to read a complete record.")
                print("filename=%s" % self.filename)
                print("bytesRemaining=%d" % bytesRemaining)

                extraBuffer = fileHandle.read(bytesRemaining)
                extraBytes = ""

                for byte in extraBuffer:
                    extraBytes += "0x%x " % byte

                print("extraBytes=%s" % extraBytes)

                break

            nxtRecord = GcdaInfo.read_record(fileHandle)

            if nxtRecord is None:
                break

            self.records.append(nxtRecord)

            curPos = fileHandle.tell()

        return

    def _save_header(self, fileHandle):

        magic = self.header.magic
        version = self.header.version
        stamp = self.header.stamp

        GcdaInfo.write_quad_char(fileHandle, magic)
        GcdaInfo.write_quad_char(fileHandle, version)
        GcdaInfo.write_uint32(fileHandle, stamp)

        return

    def _save_records(self, fileHandle):

        for record in self.records:
            GcdaInfo.write_record(fileHandle, record)

    @staticmethod
    def read_quad_char(fileHandle):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        quadByte = fileHandle.read(4)
        if len(quadByte) < 4:
            print("ERROR: Problem reading UInt32, not enough bytes left in record. quadByte=%s" % quadByte)

        return quadByte

    @staticmethod
    def read_uint32(fileHandle, packStr=GcdaConst.PACKUINT32):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        quadByte = fileHandle.read(4)
        if len(quadByte) < 4:
            print("ERROR: Problem reading UInt32, not enough bytes left in record. quadByte=%s" % quadByte)

        val, = struct.unpack(packStr, quadByte)

        return val

    @staticmethod
    def read_uint64(fileHandle, packStr=GcdaConst.PACKUINT32):
        """
            uint64:  uint32:low uint32:high
        """
        lowOrder = GcdaInfo.read_uint32(fileHandle, packStr)
        highOrder = GcdaInfo.read_uint32(fileHandle, packStr)

        val = (highOrder << 32) | lowOrder

        return val

    @staticmethod
    def read_string(fileHandle, packStr=GcdaConst.PACKUINT32):
        """
            string: uint32:0 | uint32:length char* char:0 padding
            padding: | char:0 | char:0 char:0 | char:0 char:0 char:0
        """

        wordLength = GcdaInfo.read_uint32(fileHandle, packStr)
        strLen = wordLength * 4

        strVal = fileHandle.read(strLen).rstrip(b"\0")

        return strVal

    @staticmethod
    def read_record(fileHandle, packStr=GcdaConst.PACKUINT32):
        """
            record: header data
            header: uint32:tag uint32:length
              data: item*
        """
        recordTag = GcdaInfo.read_uint32(fileHandle, packStr)
        recordLength = GcdaInfo.read_uint32(fileHandle, packStr)

        byteLen = recordLength * 4
        recordItemsData = fileHandle.read(byteLen)

        return GcdaRecord(recordTag, recordLength, recordItemsData)

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
    def write_quad_char(fileHandle, quad_char):
        """
            uint32 in quad char format
        """
        fileHandle.write(quad_char)
        return

    @staticmethod
    def write_uint32(fileHandle, val, packStr=GcdaConst.PACKUINT32):
        """
            uint32:  byte3 byte2 byte1 byte0 | byte0 byte1 byte2 byte3
        """
        fileHandle.write(struct.pack(packStr, val))
        return

    @staticmethod
    def write_uint64(fileHandle, val):
        """
            uint64:  uint32:low uint32:high
        """
        lowOrder = val & GcdaConst.LOWORDERMASK
        highOrder = (val & GcdaConst.HIGHORDERMASK) >> 32

        # Write the low order word
        GcdaInfo.write_uint32(fileHandle, lowOrder)

        # Write the high order word
        GcdaInfo.write_uint32(fileHandle, highOrder)
        return

    @staticmethod
    def write_string(fileHandle, val):
        """
            string: uint32:0 | uint32:length char* char:0 padding
            padding: | char:0 | char:0 char:0 | char:0 char:0 char:0
        """
        valLen = len(val)
        padlen = valLen % 4

        fileHandle.write(val)

        if (val[valLen - 1] == 'x00') and (padlen == 0):
            return

        fileHandle.write(GcdaConst.GCOVIO_STRINGPADDING[padlen])

        return

    @staticmethod
    def write_record(fileHandle, record):
        """
            record: header data
            header: uint32:tag uint32:length
              data: item*
        """
        recordTag = record.tag
        GcdaInfo.write_uint32(fileHandle, recordTag)

        recordLength = record.length
        GcdaInfo.write_uint32(fileHandle, recordLength)

        recordItemsData = record.items_data
        GcdaInfo.write_uint32(fileHandle, recordItemsData)

        return

    @staticmethod
    def unpack_record(record, packStr=GcdaConst.PACKUINT32):
        cpos = 0

        tag = record.header.tag
        header = record.header
        buffer = record.items_data

        if tag == GcdaConst.GCOV_TAG_FUNCTION:
            swapRecord = GcdaInfo.unpack_function_announcement(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_COUNTER_BASE:
            swapRecord = GcdaInfo.unpack_counter_base(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_OBJECT_SUMMARY:
            swapRecord = GcdaInfo.unpack_object_summary(header, buffer, cpos, packStr)
        elif tag == GcdaConst.GCOV_TAG_PROGRAM_SUMMARY:
            swapRecord = GcdaInfo.unpack_program_summary(header, buffer, cpos, packStr)
        else:
            raise IOError("Un-recognized tag (0x%x) found at record index in file." % tag)

        return swapRecord

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
        num, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)
        runs, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)
        sum_max, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
        max, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)
        summax, cpos = GcdaInfo.unpack_uint64(buffer, cpos, packStr)

        rval = GCovDataProgramSummaryRecord(header, checksum, num, runs, sum, max, summax)

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
        checksum, cpos = GcdaInfo.unpack_uint32(buffer, cpos, packStr)

        rval = GCovDataFunctionAnnouncementRecord(header, ident, checksum)

        return rval


if __name__ == "__main__":
    gcda = GcdaInfo()
    gcda.load("data/main.gcda")
    gcda.pull_records()
