import urllib.request, json, re, sys, argparse, collections


def Usage():
    print ("Usage: ./get_course.py degree faculty year output_file_path");

def write_file(output_file_name, code_dict, code_name):
    for key in sorted(code_dict):
        if code_dict[key]:
            prere = ' '.join(code_dict[key])
        else:
            prere = None
    with open(output_file_name, "w") as f:
        for key in sorted(code_dict):
            if code_dict[key]:
                prere = [f"{course} {code_name[course]}" for course in sorted(set(code_dict[key])) if course in code_name]
                for course in code_dict[key]:
                    if course not in code_name:
                        prere.append(f"{course}" )
                prere = '\n'.join(prere)
            else:
                prere = None
            if prere:
                f.write(f"Course: {key} {code_name[key]}\nprerequisite:\n{prere}\n\n")
            else:
                f.write(f"Course: {key} {code_name[key]}\n\n")

def fetch_2019(degree, faculty_code, output_file_name):
    http_prefix = "https://www.handbook.unsw.edu.au"
    code_dict = {}
    code_name = {}
    address = f"https://www.handbook.unsw.edu.au/api/content/query/+contentType:subject -subject.active:0 +subject.implementation_year:*** +subject.code:*{faculty_code}* +subject.study_level:{degree} +deleted:false +working:true/offset/0/limit/-1"
    with urllib.request.urlopen(address) as url:
        data = json.loads(url.read().decode())
        length = len(data['contentlets'])
        for num_list_course in range(length):
            code = data['contentlets'][num_list_course]['code']
            name = data['contentlets'][num_list_course]['name']
            code_dict[code] = None
            code_name[code] = name
            try:
                with urllib.request.urlopen(http_prefix+data['contentlets'][num_list_course]['URL_MAP_FOR_CONTENT']) as url2:
                    for content in url2.read().decode().split('\n'):
                        if 'prerequisite' in content.lower():
                            pre_list = re.findall('[A-Z]{4}[0-9]{4}', content)
                            pre_list = list(filter(lambda x:x != code, pre_list))
                            if pre_list:
                                code_dict[code] = pre_list
            except KeyError:
                pass
        res_dic = collections.defaultdict(list)
        for key in code_dict:
            queue = collections.deque()
            if code_dict[key] is None:
                res_dic[key] = None
            else:
                for e in code_dict[key]:
                    cs = set()
                    queue.append(e)
                    while len(queue) > 0:
                        pre = queue.pop()
                        if pre in cs:
                            continue
                        cs.add(pre)
                        if key not in res_dic:
                            res_dic[key] = [pre]
                        else:
                            res_dic[key].append(pre)
                        if pre in code_dict and code_dict[pre] is not None:
                            for e in code_dict[pre]:
                                queue.appendleft(e)
        write_file(output_file_name, res_dic, code_name)


def fetch_2018(degree, code, year, output_file):
    address = f'http://legacy.handbook.unsw.edu.au/vbook{year}/brCoursesByAtoZ.jsp?StudyLevel=' + degree + '&descr=' + code
    with urllib.request.urlopen(address) as url:
        codes = re.compile('<TD class="[a-zA-Z]*" align="left">([A-Z a-z 0-9]{8})</TD>\n\s+<TD class="[a-zA-Z]*"><A href="(.+)">([A-Za-z ]+)').findall(url.read().decode())
        codeDict = {}
        nameDict = {}
        for pair in codes:
            nameDict[pair[0]] = pair[2].rstrip()
            with urllib.request.urlopen(pair[1]) as url2:
                L = re.compile('<p>Prerequisite:([A-Z a-z 0-9.,]*)</p>').findall(url2.read().decode())
                if L != []:
                    L = re.compile('[A-Z]{4}[0-9]{4}').findall(L[0])
                if L:
                    L = list(filter(lambda x:x != pair[0], L))
                    codeDict[pair[0]] = L
                else:
                    codeDict[pair[0]] = None
        res_dic = collections.defaultdict(list)
        for key in codeDict:
            queue = collections.deque()
            if codeDict[key] is None:
                res_dic[key] = None
            else:
                for e in codeDict[key]:
                    cs = set()
                    queue.append(e)
                    while len(queue) > 0:
                        pre = queue.pop()
                        if pre in cs:
                            continue
                        cs.add(pre)
                        if key not in res_dic:
                            res_dic[key] = [pre]
                        else:
                            res_dic[key].append(pre)
                        if pre in codeDict and codeDict[pre] is not None:
                            for e in codeDict[pre]:
                                queue.appendleft(e)
        write_file(output_file, res_dic, nameDict)


def main():
    if len(sys.argv[1:]) != 4:
        Usage()
        sys.exit(1)
    degree = sys.argv[1]
    code = sys.argv[2]
    try:
        year = int(sys.argv[3])
    except:
        print ("Invalid year\n")
        sys.exit(1)
    if year > 2020 or year < 2004:
        print ("Invalid year\n")
        sys.exit(1)
    if degree.startswith("un"):
        degree = "undergraduate"
    else:
        degree = "postgraduate"
    output = sys.argv[4]
    if year >= 2019:
        fetch_2019(degree, code, output)
    else:
        fetch_2018(degree, code, year, output)



if __name__ == '__main__':
    main()