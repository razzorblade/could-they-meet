import sys
import math

# source: https://stackoverflow.com/questions/3002085/python-to-print-out-status-bar-and-percentage/3002114
def update_progress(progress):
    barLength = 20 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rProgress: [{0}] {1:.2f}% {2}".format( "="*block + " "*(barLength-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()


# source: https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
def get_smart_file_size(bytes_size):
    if bytes_size == 0:
        return "0B"
    size_name = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    i = int(math.floor(math.log(bytes_size, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_size / p, 2)
    return "%s %s" % (s, size_name[i])

def max_clamp(num, max_num):
    if num > max_num:
        return max_num
    return num