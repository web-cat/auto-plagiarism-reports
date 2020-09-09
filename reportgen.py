from html.parser import HTMLParser
import argparse
import mosspy.mosspy as mosspy
import os
import zipfile
import re
import subprocess
import shutil
import sys

m_values = [2, 3, 5, 10, 15]
threshold = 40
sus_students = dict()

parser = argparse.ArgumentParser()
parser.add_argument('-o', dest='outputdir', type=str, default="./results/")
parser.add_argument('-r', dest='rootdir', type=str, default="../")
parser.add_argument('-c', dest='crn', type=str, default="")
parser.add_argument('-a', dest='assignment', type=str, default="")
args = parser.parse_args()
crn = args.crn
assignment = args.assignment
rootdir = args.rootdir
outputdir = args.outputdir
projoutput = os.path.join(outputdir, assignment)
print("crn is: " + args.crn)
print("assignment is: " + args.assignment)
print("root directory is: " + args.rootdir)
print("outputdir is: " + args.outputdir)

def listfiles(folder):
    for root, folders, files in os.walk(folder):
        for filename in folders + files:
            yield os.path.join(root, filename)

# Put your moss submission id in a file "moss_id.txt"
userid = 0
try:
    f = open("moss_id.txt")
    userid = int(f.read())
    f.close()
except Exception as e:
    print(e)
    userid = 0
if userid == 0:
    print("Could not get a valid moss user id from file moss_id.txt")
    exit()

m = mosspy.Moss(userid, "java")

if crn != "":
    toppath = os.path.join(rootdir, crn, assignment)
    for uuid in os.listdir(toppath):
        maxdir = 0
        nextpath = os.path.join(toppath, uuid)
        for sub in os.listdir(nextpath):
            if int(sub) > maxdir:
                maxdir = int(sub)
        bottompath = os.path.join(nextpath, str(maxdir))
        for fname in os.listdir(bottompath):
            if fname.endswith(".zip"):
                with zipfile.ZipFile(bottompath+"/"+fname) as zip_ref:
                    zip_ref.extractall(bottompath)

        for root, dirs, files in os.walk(bottompath):
            for name in files:
                if name.endswith(".java"):
                    m.addFile(os.path.join(root,name))

        for fname in os.listdir(bottompath):
            print(fname)
            if fname.endswith(".java"):
                m.addFile(os.path.join(bottompath, fname))
            
print(m.files)
m.setDirectoryMode(1)
for mval in m_values:
    sus_students[mval] = dict()
    m.setIgnoreLimit(mval)
    url = m.send()
    print("m = " + str(mval) + " url: " + url)
    os.makedirs(projoutput, exist_ok=True)
    m.saveWebPage(url, projoutput+"/"+str(mval)+ "_report.html")
    f = open(projoutput+"/"+str(mval)+ "_report.html", "r")
    # html file specific handling
    useful_lines = f.readlines()[14:-5]
    print(useful_lines[0])
    for i in range(0, len(useful_lines), 3):
        l1_score = 0
        l2_score = 0
        line1 = useful_lines[i]
        line2 = useful_lines[i+1]
        l1_re = re.search('(\d+)%', line1)
        if l1_re:
            l1_score = int(l1_re.group(1))
        l2_re = re.search('(\d+)%', line2)
        if l2_re:
            l2_score = int(l2_re.group(1))
        score_avg = (l1_score + l2_score) / 2
        if score_avg >= threshold:
            path1 = re.search('">(.*?/) \\(\d+%', line1)
            path1 = path1.group(1)
            sus_students[mval][path1] = dict()
            path2 = re.search('">(.*?/) \\(\d+%', line2)
            path2 = path2.group(1)
            sus_students[mval][path1][path2] = score_avg

    
    f.close()
for run in sus_students:
    for s1 in sus_students[run]:
        s1nre = re.search(assignment + '\/(.*?)\/', s1)
        s1n = s1nre.group(1)
        print(s1n)
        for s2 in sus_students[run][s1]:
            s2nre = re.search(assignment + '\/(.*?)\/', s2)
            s2n = s2nre.group(1)
            print("\t"+s2n)
            finalname = s1n + "_" + s2n
            try:
                os.makedirs(os.path.join(projoutput, finalname), exist_ok=True)
            except OSError:
                pass
            try:
                s1d = os.path.join(projoutput, finalname, s1n)
                s2d = os.path.join(projoutput, finalname, s2n)
                os.makedirs(s1d, exist_ok=True)
                os.makedirs(s2d, exist_ok=True)
            except Exception:
                pass
            try:
                shutil.copytree(s1, s1d+"/result")
                shutil.copytree(s2, s2d+"/result")
            except Exception as e:
                print(e)
                #pass

print("all done!")
print(sus_students)
