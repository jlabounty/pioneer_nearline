import os
import sys
# import html 
from datetime import datetime

def create_index(indir, outfile='static/file-index.html'):
    with open(outfile, 'w') as f:
        f.write("<!DOCTYPE html>\n")
        f.write('<html>\n')
        f.write('<head> \n')
        f.write( '<link rel="stylesheet" target=\"_blank\" href="assets/css/lists.css">\n')
        f.write('</head>\n')
        f.write('<body>\n')
        f.write("<h1> Index of merged histogram files (updated: \n")
        f.write(f'{datetime.now()} \n')
        f.write(") </h1>\n")
        f.write("<h> Click on the links below to download nearline files: </h>\n")
        f.write("<a href='browse/processed/run_db.csv'> <h3>Run Conditions CSV</h3> </a>")
        f.write("<div>\n")
        f.write("<OL>\n")

        run_folders = os.listdir(indir)
        run_folders.sort()
        for ri in run_folders:
            if('.csv') in ri or 'tar' in ri:
                continue
            run = int(ri.split("run")[1])
            run_folder = os.path.join(indir, ri,'data')
            print(run_folder)
            subruns = os.listdir(run_folder)
            subruns.sort()

            f.write(f'<li> Run {run} (tarball <a href="/runs/{run}/{run+1}" id="{run}">here<a/>) \n')
            f.write("<ul> \n")
            for si in subruns:
                print(si)
                subrun = si.split("subrun")[-1]
                f.write(f"<li> Run {run} subrun {subrun}")
                thisdir = os.path.join(run_folder, si)
                print(thisdir)
                # f.write("<UL>\n")
                for file in os.listdir(thisdir):
                    thisfile = os.path.join(thisdir[3:], file)
                    f.write(f"<p>   → <a href='browse/{thisfile}'>{file}")
                    if('.root' in file):
                        f.write(f' (<a href="/jsroot?file=browse/{thisfile}">Online viewer<a/>)')
                    f.write('<p/><a/>')
                # f.write("<UL/>\n")
                f.write("</li>")
            f.write("</ul> \n")
        # for i in range(1000):
        #     f.write(f"<li> hi {i} <li/>")

        f.write('</OL> \n')
        f.write('</div> \n')
        f.write('<body/> \n')
        f.write('<html/> \n')
