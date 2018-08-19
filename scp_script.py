import paramiko
import sys
import re
import scp
import time

if len(sys.argv) != 2:
    print("Argument error")
    sys.exit(1)

HOST = "192.168.0.112"
USERNAME = "pi"
command = """ls -R /mnt/PIHDD/Videos/ | awk '
/:$/&&f{s=$0;f=0}
/:$/&&!f{sub(/:$/,"");s=$0;f=1;next}
NF&&f{ print s"/"$0 }'"""
regex = ".*%s.*\.(mkv|webm|flv|vob|ogg|ogv|drc|gifv|mng|avi|mov|qt" \
        "|wmv|yuv|rm|rmvb|asf|amv|mp4$|m4v|mp|m?v|svi|3gp|flv|f4v)$"

""" SSH connect """
try:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, 22, USERNAME)
except Exception as e:
    print("SSH error: {}".format(e))
    sys.exit(1)


""" Get all file names """
try:
    stdin, stdout, stderr = client.exec_command(command)
    str_stdout = stdout.read().decode("utf-8")
    str_stderr = stderr.read().decode("utf-8")

    client.close()

    if str_stderr:
        raise Exception(str_stderr)

    file_paths = str_stdout.split("\n")

    if sys.argv[1] == "-a":
        all_files = [file_path for file_path in file_paths if re.search(regex % "", file_path)]
        for file_path in all_files:
            name = file_path.split("/")[-1]
            print(name)
        sys.exit(0)

    filtered_file_paths = [file_path for file_path in file_paths if re.search(regex % sys.argv[1],
                                                                              file_path, re.IGNORECASE)]

    if not filtered_file_paths:
        raise Exception("No files found!")


except Exception as e:
    print("Command issue: {}".format(e))
    sys.exit(1)


""" Confirm files to scp """
print("The following files will be transfered: \n")
for file_path in filtered_file_paths:
    print("\t{}".format(file_path))
print("\n")
while True:
    input_arg = input("Proceed?(y/n)")
    if input_arg == "y":
        break
    elif input_arg == "n":
        sys.exit(0)
    else:
        print("input 'y' or 'n'")


""" Do the scp  """
try:
    # progress callback that prints the current percentage completed for the file
    def progress(filename, size, sent):
        sys.stdout.write("%s\'s progress: %.2f%%   \r" % (filename, float(sent) / float(size) * 100))


    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, 22, USERNAME)

    # SCPCLient takes a paramiko transport and progress callback as its arguments.
    scp_client = scp.SCPClient(client.get_transport(), progress=progress)

    for file_path in filtered_file_paths:
        _, name = file_path.split("/Videos/")
        print("Downlading: {}".format(name))

        scp_client.get(file_path)
        # Should now be printing the current progress of your put function.
        print("OK")

        time.sleep(1)

    client.close()
    scp_client.close()


except Exception as e:
    print("SCP error: {}".format(e))
    sys.exit(1)


print("\nDownload/s complete\n")
print(""" ______         ,-----.    ,---.   .--.    .-''-.   
|    _ `''.   .'  .-,  '.  |    \  |  |  .'_ _   \  
| _ | ) _  \ / ,-.|  \ _ \ |  ,  \ |  | / ( ` )   ' 
|( ''_'  ) |;  \  '_ /  | :|  |\_ \|  |. (_ o _)  | 
| . (_) `. ||  _`,/ \ _/  ||  _( )_\  ||  (_,_)___| 
|(_    ._) ': (  '\_/ \   ;| (_ o _)  |'  \   .---. 
|  (_.\.' /  \ `"/  \  ) / |  (_,_)\  | \  `-'    / 
|       .'    '. \_/``".'  |  |    |  |  \       /  
'-----'`        '-----'    '--'    '--'   `'-..-' """)
sys.exit(0)
