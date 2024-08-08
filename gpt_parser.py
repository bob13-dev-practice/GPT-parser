import struct
import sys

_PTE_STRUCT = "<16s16sQQLL72s"
_GUID_STRUCT = "<4s2s2s2s6s"

SECTOR_SIZE = 512
MAX_PARTITION_CNT = 128
PARTITION_TABLE_OFFSET = 32
PARTITION_ENTRY_SIZE = 128
FILESYSTEM_SIZE = 3

PARTITION_TYPES  = {
    "NTFS" : b'\xEB\x52\x90',
    "FAT32" : b'\xEB\x3C\x90',
}

def get_filesystem_type(partition_type):
    if partition_type == PARTITION_TYPES["FAT32"]:
        return "FAT32"
    elif partition_type == PARTITION_TYPES["NTFS"]:
        return "NTFS"
    return None

def format_guid(guid_bytes):
    unpacked_data = struct.unpack(_GUID_STRUCT, guid_bytes)
    final_bytes = (
        unpacked_data[0][::-1] +
        unpacked_data[1][::-1] +
        unpacked_data[2][::-1] +
        unpacked_data[3] +
        unpacked_data[4]
    )
    return final_bytes.hex().upper()

def read_partition_entry(entry):
    partition_table_entry = struct.unpack(_PTE_STRUCT, entry)
    GUID = format_guid(partition_table_entry[0]) # GUID 바이트
    first_LBA = partition_table_entry[2]  # 시작 주소
    last_LBA = partition_table_entry[3]  # 끝 주소
    return GUID, first_LBA, last_LBA

def read_gpt(file_path):
    with open(file_path, 'rb') as f:
        f.seek(2 * SECTOR_SIZE)
        gpt = f.read(MAX_PARTITION_CNT * PARTITION_ENTRY_SIZE)
        partitions = []

        for i in range(MAX_PARTITION_CNT):
            entry = gpt[i * PARTITION_ENTRY_SIZE : (i + 1) * PARTITION_ENTRY_SIZE]
            GUID, first_LBA, last_LBA = read_partition_entry(entry)

            f.seek(first_LBA * SECTOR_SIZE)
            partition_type = f.read(FILESYSTEM_SIZE)

            fs_type = get_filesystem_type(partition_type)
            if fs_type:
                start_sector = first_LBA * SECTOR_SIZE
                partition_size = (last_LBA - first_LBA + 1)
                partitions.append((GUID, fs_type, start_sector, partition_size))

        return partitions

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gpt_parser.py <evidence_image>")
        sys.exit(1)

    evidence_image = sys.argv[1]
    partitions = read_gpt(evidence_image)

    for GUID, fs_type, start_sector, partition_size in partitions:
        print(f"{GUID} {fs_type} {start_sector} {partition_size}")


if __name__ == "__main__":
    main()