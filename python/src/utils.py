import sys

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