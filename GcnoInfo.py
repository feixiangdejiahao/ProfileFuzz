import os
import GcovConst
from GcovIO import GcovIO


class GcnoInfo:
    def __init__(self, filename=None, header=None, records=None):
        self.source_file_name = None
        self.file_path = None
        self.pack_str32 = GcovConst.PACKUINT32
        self.filename = filename
        self.header = header
        self.records = records
        return

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
        cwd_length = GcovIO.read_uint32(file_handle)
        cwd = file_handle.read(cwd_length * 4)
        unexc_blocks = GcovIO.read_uint32(file_handle)
        self.header = GcnoFileHeader(magic, version, stamp, cwd, unexc_blocks)

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

            nxtRecord = GcnoInfo.read_record(file_handle)

            if nxtRecord is None:
                break

            self.records.append(nxtRecord)

            cur_pos = file_handle.tell()

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
        if isinstance(record, GcnoRecord):
            swap_record = GcnoInfo.unpack_record(record, self.pack_str32)

            self.records[index] = swap_record
            del record
            record = swap_record

        return record

    @staticmethod
    def unpack_record(record, packStr=GcovConst.PACKUINT32):
        cpos = 0

        tag = record.header.tag
        header = record.header
        buffer = record.items_data

        if tag == GcovConst.GCOV_TAG_FUNCTION:
            swap_record = GcnoInfo.unpack_function_announcement(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_ARCS:
            swap_record = GcnoInfo.unpack_arc_set(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_LINES:
            swap_record = GcnoInfo.unpack_line_set(header, buffer, cpos, packStr)
        elif tag == GcovConst.GCOV_TAG_BLOCKS:
            swap_record = GcnoInfo.unpack_basic_block(header, buffer, cpos, packStr)
        else:
            raise IOError("Un-recognized tag (0x%x) found in file." % (tag))

        return swap_record

    @staticmethod
    def unpack_function_announcement(header, buffer, pos, packStr=GcovConst.PACKUINT32):
        """
            announce_function: header uint32:ident uint32:checksum string:name string:source uint32:lineno
        """
        cpos = pos
        ident, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        lineno_checksum, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        cfg_checksum, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        function_name_length, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        function_name, cpos = GcovIO.unpack_string(buffer, cpos, function_name_length)
        artificial, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        source_length, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        source, cpos = GcovIO.unpack_string(buffer, cpos, source_length)
        start_lineno, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        start_columnno, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        end_lineno, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        end_columnno, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)

        rval = GcovNoteFunctionAnnouncementRecord(header, ident, lineno_checksum, cfg_checksum, function_name,
                                                  artificial,
                                                  source, start_lineno, start_columnno, end_lineno, end_columnno)

        return rval

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

        record_length = int(hex_str, 16)
        byte_len = record_length * 4
        record_items_data = file_handle.read(byte_len)

        return GcnoRecord(record_tag, record_length, record_items_data)

    @staticmethod
    def unpack_arc_set(header, buffer, pos, packStr=GcovConst.PACKUINT32):
        """
            arcs: header uint32:block_no arc*
                arc:  uint32:dest_block uint32:flags
        """
        cpos = pos

        blockNumber, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)

        arcCount = int((header.length - 1) / 2)
        arcSet = []

        while arcCount > 0:
            destblock, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
            flags, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)

            arcEntry = GcovGraphArc(destblock, flags)
            arcSet.append(arcEntry)

            arcCount -= 1

        rval = GcovNoteArcSetRecord(header, blockNumber, arcSet)

        return rval

    @staticmethod
    def unpack_line_set(header, buffer, pos, packStr=GcovConst.PACKUINT32):
        """
                lines: header uint32:block_no line* => termline

            A unpacked line could look like any of the below items.  It is simply a uint32 followed by a string

                line:  uint32:0 string:filename
                       uint32:line_no
                       uint32:0, string:NULL
        """
        cpos = pos

        blockNumber, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        artifical, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        source_name_length, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)
        source_name, cpos = GcovIO.unpack_string(buffer, cpos, source_name_length)
        lineset = []

        while True:
            lineno, cpos = GcovIO.unpack_uint32(buffer, cpos, packStr)

            if lineno == 0:
                break

            lineitem = GcovGraphLine(lineno)
            lineset.append(lineitem)

        rval = GcovNoteLineSetRecord(header, blockNumber, lineset)
        return rval

    @staticmethod
    def unpack_basic_block(header, buffer, pos, packStr=GcovConst.PACKUINT32):
        """
            header uint32:flags*
        """
        cpos = pos

        blockCount, _ = GcovIO.unpack_uint32(buffer, cpos, packStr)
        rval = GcovNoteBasicBlocksRecord(header, blockCount)

        return rval


class GcnoFileHeader:
    """
        uint32:magic
        uint32:version
        uint32:stamp
        uint32:unexec_blocks
    """

    def __init__(self, magic, version, stamp, cwd, unexec_blocks=None):
        self.magic = magic
        self.version = version
        self.stamp = stamp
        self.cwd = cwd
        self.unexec_blocks = unexec_blocks
        return


class GcnoRecord:
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
        self.header = GcnoRecordHeader(tag, length)
        self.items_data = items_data
        return

    def __str__(self):
        tagKey = self.header.tag
        tagType = str(tagKey)
        if tagKey in GcovConst.GCOVIO_TAGTYPE_STR:
            tagType = GcovConst.GCOVIO_TAGTYPE_STR[tagKey]
        strval = "Type=%s Length=%d Data=%r" % (tagType, self.header.length, self.items_data)
        return strval


class GcnoRecordHeader:
    """
        uint32:tag uint32:length
    """

    def __init__(self, tag, length):
        self.tag = tag
        self.length = length
        return


class GcovNoteFunctionAnnouncementRecord:
    """
        header uint32:ident uint32:checksum string:name string:source uint32:lineno
    """

    def __init__(self, header, ident, lineno_checksum, cfg_checksum, name, artificial, source, start_lineno,
                 start_columnno, end_lineno, end_columnno):
        self.header = header
        self.ident = ident
        self.lineno_checksum = lineno_checksum
        self.cfg_checksum = cfg_checksum
        self.name = name
        self.artificial = artificial
        self.source = source
        self.start_lineno = start_lineno
        self.start_columnno = start_columnno
        self.end_lineno = end_lineno
        self.end_columnno = end_columnno
        return

    def print(self):
        print("Function: Ident=%d LineNoCheckSum%d CfgCheckSum=%d LineNo=%d Name=%s Source%s" % (
            self.ident, self.lineno_checksum, self.cfg_checksum, self.line_no, self.name, self.source))
        return


class GcovNoteArcSetRecord:
    """
        arcs: header uint32:block_no arc*
    """

    def __init__(self, header, blockNumber, arcs):
        self.header = header
        self.block_number = blockNumber
        self.arcs = arcs

    def print(self):
        print("ArcsRecord: BlockNumber=%d" % self.block_number)
        return


class GcovNoteLineSetRecord:
    """
        lines: header uint32:block_no line* => termline
            line:  uint32:line_no | uint32:0 string:filename
            termline: uint32:0 string:NULL
    """

    def __init__(self, header, blockNumber, lines):
        self.header = header
        self.block_number = blockNumber
        self.lines = lines

    def print(self):
        print("LinesRecord: BlockNumber=%d" % self.block_number)
        return


class GcovGraphArc:
    """
        uint32:dest_block uint32:flags
    """

    def __init__(self, destBlock, flags):
        self.dest_block = destBlock
        self.flags = flags
        self.arc_id = None
        self.counter = None

        self.has_flag_fake = ((flags & GcovConst.GCOV_FLAG_ARC_FAKE) > 0)
        self.has_flag_fall_through = ((flags & GcovConst.GCOV_FLAG_ARC_FALLTHROUGH) > 0)
        self.has_flag_on_tree = ((flags & GcovConst.GCOV_FLAG_ARC_ON_TREE) > 0)

        self.is_relevant_branch = False
        self.is_return_branch = False
        self.is_exception_branch = False

    def print(self):
        print("        GCovGraphArc:")
        print("            DestBlock=%d" % self.dest_block)
        print("            Flags=%d" % self.flags)
        print("            ArcId=%d" % self.arc_id)
        print("            Counter=%d" % self.counter)
        print("            HasFlagFake=%d" % self.has_flag_fake)
        print("            HasFlagFallThrough=%d" % self.has_flag_fall_through)
        print("            HasFlagOnTree=%d" % self.has_flag_on_tree)
        print("            IsRelevantBranch=" + self.is_relevant_branch)
        print("            IsExceptionBranch=" + self.is_exception_branch)

        return


class GcovGraphLine:
    """
        uint32:line_no string:(filename | linestr | NULL)
    """

    def __init__(self, number):
        self.number = number

    def print(self):
        print("        GCovGraphLine:")
        print("            Number=%d" % self.number)
        return


class GcovGraphBlock:
    """
    """

    def __init__(self, blockNumber):
        self.block_number = blockNumber
        self.lines = None
        self.line_no = 0

        self.arcs_successors = []
        self.arcs_predecessors = []

        self.is_branch_landing = False
        self.is_call_site = False
        self.is_loop = False
        self.is_exception_landing = False
        self.is_return_landing = False
        self.has_relevant_branches = False
        return

    def print(self):
        print("    GCovGraphBlock (%d):" % self.block_number)
        print("        HasRelevantBranches=%r" % self.has_relevant_branches)

        if self.lines is not None:
            for line in self.lines:
                line.Print()
            print("")

        return


class GcovNoteBasicBlocksRecord:
    def __init__(self, header, block_count):
        self.header = header
        self.block_count = block_count
        return

    def print(self):
        print("BasicBlock: BlockCount=%d" % (self.block_count))
        return
