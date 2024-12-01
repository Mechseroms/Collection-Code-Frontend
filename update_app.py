import sys, json, psutil, requests, tempfile, os, zipfile, signal

def update_app(url, external_path):
    print(url)
    result = requests.get(url)
    print(external_path)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(temp_dir)
        with open(f"{temp_dir}/temp.zip", "wb") as file:
            file.write(result.content)
        with zipfile.ZipFile(f"{temp_dir}/temp.zip", 'r') as zip_ref:
            for member in zip_ref.namelist():
                print(member)
                filepath = os.path.join(external_path, member)
                os.remove(filepath) if os.path.exists(filepath) else None  # Remove if exists
            zip_ref.extractall(external_path)
        
        with open('log.txt', "w+") as file:
            file.write(str("updated"))

try:
    test =psutil.Process(int(sys.argv[1]))
    os.kill(int(sys.argv[1]), signal.SIGTERM)
except psutil.NoSuchProcess as e:
    try:
        update_app(url=sys.argv[2], external_path=sys.argv[3])
    except Exception as e:
        test = str(e)

with open("log.txt", "w+") as file:
    file.write(json.dumps(test))

sys.exit()
